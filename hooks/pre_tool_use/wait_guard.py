#!/usr/bin/env python3
"""Deny in-turn waiting on GitHub; hand back the one watcher grammar.

Waiting on a PR has one shape: babysit's pr-watch as a fireAndForget Execute,
whose exit wakes the agent with the event to handle. This guard rejects the two
habits that replace it:

- a sleep or watch primitive in the same command as a GitHub PR or CI query
  (a poll loop, foreground or background);
- a foreground blocking watch (`gh run watch`, `gh pr checks --watch`).

It tokenizes with the shared shell lexer and fails open on anything else.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils import (  # type: ignore
    HookInputError,
    PreToolUseInput,
    exit,
    get_toml_section,
    load_toml,
    read_input_as,
)
from utils.shell import (  # type: ignore
    ASSIGNMENT_RE,
    normalize_tokens,
    segments,
    strip_heredocs,
    tokenize,
)

HOOK_EVENT = "PreToolUse"
PR_WATCH = "~/.agents/skills/babysit/scripts/pr-watch <pr> [--repo owner/name]"

_KEYWORDS = {"do", "then", "else", "elif", "while", "until", "if", "{", "(", "!"}
_PREFIXES = {"command", "exec", "time", "nohup"}
_WAITS = {"sleep", "watch"}
_GH_QUERIES = {
    ("pr", "checks"),
    ("pr", "view"),
    ("pr", "status"),
    ("run", "view"),
    ("run", "list"),
    ("run", "watch"),
}
_API_MARKERS = ("pulls", "check-runs", "check-suites", "actions/runs", "/status")


def _head(segment: list[str]) -> list[str]:
    tokens = normalize_tokens(segment)
    index = 0
    while index < len(tokens) and (
        tokens[index] in _KEYWORDS
        or tokens[index] in _PREFIXES
        or ASSIGNMENT_RE.fullmatch(tokens[index])
    ):
        index += 1
    return tokens[index:]


def _is_wait(tokens: list[str]) -> bool:
    return bool(tokens) and Path(tokens[0]).name in _WAITS


def _gh_args(tokens: list[str]) -> list[str] | None:
    return tokens[1:] if tokens and Path(tokens[0]).name == "gh" else None


def _is_gh_query(tokens: list[str]) -> bool:
    args = _gh_args(tokens)
    if not args:
        return False
    if tuple(args[:2]) in _GH_QUERIES:
        return True
    return args[0] == "api" and any(
        marker in arg for arg in args[1:] for marker in _API_MARKERS
    )


def _is_blocking_watch(tokens: list[str]) -> bool:
    args = _gh_args(tokens) or []
    return args[:2] == ["run", "watch"] or (
        args[:2] == ["pr", "checks"] and "--watch" in args
    )


def _wrapped(tokens: list[str]) -> list[str]:
    """The command `watch` reruns, from its first gh token."""
    names = [Path(token).name for token in tokens]
    return tokens[names.index("gh") :] if "gh" in names else []


def _violation(command: str, *, fire_and_forget: bool) -> str | None:
    heads = [_head(segment) for segment in segments(tokenize(strip_heredocs(command)))]
    heads += [_wrapped(head) for head in heads if _is_wait(head)]
    if any(map(_is_wait, heads)) and any(map(_is_gh_query, heads)):
        return "this polls GitHub state with sleep or watch"
    if not fire_and_forget and any(map(_is_blocking_watch, heads)):
        return "this blocks the turn on a GitHub watch"
    return None


def _enabled() -> bool:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--config-file", default="")
    config_path = parser.parse_args(sys.argv[1:]).config_file
    if not config_path:
        return True
    section = get_toml_section(load_toml(config_path), "hooks", "pre_tool_use", "waits")
    return section.get("enabled") is not False


def main() -> None:
    try:
        hook_input = read_input_as(PreToolUseInput)
    except HookInputError as exc:
        exit(1, text=f"[wait-guard] input error: {exc}", to_stderr=True)

    command = hook_input.tool_input.get("command")
    if hook_input.tool_name != "Execute" or not isinstance(command, str):
        exit(hook_event_name=HOOK_EVENT)

    try:
        reason = (
            _violation(
                command,
                fire_and_forget=bool(hook_input.tool_input.get("fireAndForget")),
            )
            if _enabled()
            else None
        )
    except Exception:
        exit(hook_event_name=HOOK_EVENT)

    if reason is None:
        exit(hook_event_name=HOOK_EVENT)

    exit(
        decision="deny",
        reason=(
            f"[wait-guard] {reason}.\n\n"
            "Waiting on a PR has one shape. Start\n\n"
            f"    {PR_WATCH}\n\n"
            "as a fireAndForget Execute and end your turn: its exit wakes you "
            "with the event to handle, and it never reports the same event twice "
            "(babysit skill). For a workflow run with no PR, run "
            "`gh run watch <run-id> --exit-status` as fireAndForget. Never sleep "
            "or loop on GitHub state."
        ),
        hook_event_name=HOOK_EVENT,
    )


if __name__ == "__main__":
    raise SystemExit(main())
