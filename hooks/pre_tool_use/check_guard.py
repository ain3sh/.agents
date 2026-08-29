#!/usr/bin/env python3
"""Require validators to use the one foreground check-runner grammar.

Accepted shape:

    ~/.agents/scripts/run-check <label> \
      [--cwd <directory>] [--env KEY=VALUE]... -- <validator argv...>

The hook tokenizes with Python's standard shell lexer. It does not interpret,
repair, or reconstruct arbitrary shell. A check command either speaks the
accepted grammar or is denied with the grammar itself.
"""

from __future__ import annotations

import argparse
import re
import shlex
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

HOOK_EVENT = "PreToolUse"
RUNNER = "~/.agents/scripts/run-check"
RUNNER_PATH = Path.home() / ".agents" / "scripts" / "run-check"
CANONICAL = (
    f"{RUNNER} <label> [--cwd <directory>] [--env KEY=VALUE]... "
    "-- <same scoped validator argv...>"
)

_SHELL_PUNCTUATION = "|&;<>\n"
_ASSIGNMENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*=.*")

_PREFIX = (
    r"(?:(?:command|exec|rtk|time)\s+)*"
    r"(?:(?:flock|nice|ionice|timeout)(?:\s+\S+){1,3}\s+)?"
    r"(?:env(?:\s+[A-Za-z_][A-Za-z0-9_]*=\S+)*\s+)?"
    r"(?:(?:npx|pnpm|yarn|bun|bunx|uvx|uv\s+run)\s+)?"
)

_RUNNERS = (
    r"(?:(?:npm|pnpm|yarn|bun)\s+(?:run\s+)?"
    r"(?:tests?(?::[\w-]+)?|lint|type-?checks?|checks?|build)\b"
    r"|turbo\s+run\s+[\w:.-]*(?:test|lint|typecheck|check|build)"
    r"|go\s+test\b"
    r"|cargo\s+(?:test|clippy|check)\b"
    r"|make\s+\S*(?:test|check|lint)s?(?:[-_][\w]+)*(?=\s|$))"
)


def _validator_re(tools: list[str]) -> re.Pattern[str]:
    escaped = sorted(
        (re.escape(tool) for tool in tools if tool.strip()),
        key=len,
        reverse=True,
    )
    tools_alt = rf"(?:(?:\S*/)?(?:{'|'.join(escaped)}))\b|" if escaped else ""
    return re.compile(rf"^\s*{_PREFIX}(?:{tools_alt}{_RUNNERS})")


def _tokenize(command: str) -> list[str]:
    lexer = shlex.shlex(
        command,
        posix=False,
        punctuation_chars=_SHELL_PUNCTUATION,
    )
    lexer.commenters = ""
    lexer.whitespace = " \t\r"
    lexer.whitespace_split = True
    return list(lexer)


def _normalize_token(token: str) -> str:
    try:
        values = shlex.split(token, posix=True)
    except ValueError:
        return token
    return values[0] if len(values) == 1 else token


def _normalize_tokens(tokens: list[str]) -> list[str]:
    return [_normalize_token(token) for token in tokens]


def _is_shell_operator(token: str) -> bool:
    return (
        token == "\n"
        or bool(token)
        and all(char in _SHELL_PUNCTUATION for char in token)
    )


def _is_segment_separator(token: str) -> bool:
    return _is_shell_operator(token) and (
        "\n" in token or ";" in token or "&&" in token or "||" in token
    )


def _segments(tokens: list[str]) -> list[list[str]]:
    segments: list[list[str]] = []
    current: list[str] = []
    for token in tokens:
        if _is_segment_separator(token):
            if current:
                segments.append(current)
                current = []
            continue
        current.append(token)
    if current:
        segments.append(current)
    return segments


def _is_run_check(tokens: list[str]) -> bool:
    return bool(tokens) and Path(_normalize_token(tokens[0])).name == "run-check"


def _is_canonical_run_check(token: str) -> bool:
    normalized = _normalize_token(token)
    return normalized in {RUNNER, str(RUNNER_PATH)}


def _run_check_index(tokens: list[str]) -> int | None:
    normalized = _normalize_tokens(tokens)
    index = 0
    while index < len(normalized) and _ASSIGNMENT_RE.fullmatch(normalized[index]):
        index += 1
    if index < len(normalized) and Path(normalized[index]).name == "run-check":
        return index
    return None


def _validator_tokens(tokens: list[str]) -> list[str]:
    index = 0
    while index < len(tokens) and _ASSIGNMENT_RE.fullmatch(tokens[index]):
        index += 1
    return tokens[index:]


def _is_validator(tokens: list[str], validator_re: re.Pattern[str]) -> bool:
    command = _validator_tokens(_normalize_tokens(tokens))
    return bool(command) and bool(validator_re.match(" ".join(command)))


def _valid_run_check(tokens: list[str]) -> bool:
    if len(tokens) < 4 or not _is_run_check(tokens):
        return False

    tokens = _normalize_tokens(tokens)
    label = tokens[1]
    if not label or label.startswith("-"):
        return False

    index = 2
    while index < len(tokens):
        token = tokens[index]
        if token == "--":
            return bool(tokens[index + 1 :])
        if token == "--cwd":
            if index + 1 >= len(tokens):
                return False
            index += 2
            continue
        if token == "--env":
            if (
                index + 1 >= len(tokens)
                or _ASSIGNMENT_RE.fullmatch(tokens[index + 1]) is None
            ):
                return False
            index += 2
            continue
        return False
    return False


def _violation(
    command: str,
    *,
    fire_and_forget: bool,
    validator_re: re.Pattern[str],
) -> str | None:
    tokens = _tokenize(command)
    segments = _segments(tokens)
    operators = [token for token in tokens if _is_shell_operator(token)]

    run_check_segments = [
        (segment, index)
        for segment in segments
        if (index := _run_check_index(segment)) is not None
    ]
    if run_check_segments:
        if fire_and_forget:
            return "checks must stay attached in the foreground"
        segment, index = run_check_segments[0]
        if len(segments) != 1 or operators or index != 0:
            return "run-check must be the entire shell command"
        if not _is_canonical_run_check(segment[0]):
            return "checks must invoke the canonical run-check path"
        if not _valid_run_check(segment):
            return "run-check arguments do not match the accepted grammar"
        return None

    if any(_is_validator(segment, validator_re) for segment in segments):
        return "validator commands must use run-check"
    return None


def _parse_args(argv: list[str]) -> str:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--config-file", default="")
    return parser.parse_args(argv).config_file


def _section() -> dict[str, object] | None:
    config_path = _parse_args(sys.argv[1:])
    if not config_path:
        return {}
    config = load_toml(config_path)
    section = get_toml_section(config, "hooks", "pre_tool_use", "checks")
    return None if section.get("enabled") is False else section


def _tools(section: dict[str, object]) -> list[str]:
    tools = section.get("tools")
    if not isinstance(tools, list):
        return []
    return [tool for tool in tools if isinstance(tool, str)]


def main() -> None:
    try:
        hook_input = read_input_as(PreToolUseInput)
    except HookInputError as exc:
        exit(1, text=f"[check-guard] input error: {exc}", to_stderr=True)

    if hook_input.tool_name != "Execute":
        exit(hook_event_name=HOOK_EVENT)

    command = hook_input.tool_input.get("command")
    if not isinstance(command, str) or not command.strip():
        exit(hook_event_name=HOOK_EVENT)

    try:
        section = _section()
        if section is None:
            exit(hook_event_name=HOOK_EVENT)
        reason = _violation(
            command,
            fire_and_forget=bool(hook_input.tool_input.get("fireAndForget")),
            validator_re=_validator_re(_tools(section)),
        )
    except SystemExit:
        raise
    except Exception:
        exit(hook_event_name=HOOK_EVENT)

    if reason is None:
        exit(hook_event_name=HOOK_EVENT)

    exit(
        decision="deny",
        reason=(
            f"[check-guard] {reason}.\n\n"
            "Use the only accepted check shape:\n\n"
            f"    {CANONICAL}\n\n"
            "run-check owns cwd, environment, foreground execution, complete "
            "live output, logging, and the validator's exact exit code. Do not "
            "compose shell operators, redirects, assignments, or polling around it."
        ),
        hook_event_name=HOOK_EVENT,
    )


if __name__ == "__main__":
    raise SystemExit(main())
