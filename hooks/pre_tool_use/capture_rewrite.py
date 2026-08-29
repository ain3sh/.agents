#!/usr/bin/env python3
"""Enforce file-first capture of check output before inline filtering.

The anti-pattern this kills:

    npx vitest run ... 2>&1 | rg "FAIL|Tests " | head -6

An inline filter guesses in advance -- and irrevocably -- which slice of the
output matters. A wrong guess destroys the evidence, and the only recovery is
re-running the whole suite with a new guess. The pipe also lies: ``$?`` after
a pipeline is the last filter's exit code, not the check's, and ``head``
closing the pipe early can SIGPIPE-kill the runner mid-suite.

One detector, one corrected command, capability-gated delivery (registered
for both PreToolUse and PostToolUse on Execute):

- **Interactive PreToolUse**: deny with the exact tee'd re-run command in the
  reason. The model retypes the correct pattern itself -- it knows the log
  path and pre-complies for the rest of the session.
- **Exec PreToolUse**: pass through. ``droid exec`` drops ``updatedInput``
  and treats deny as fail-fast fatal (both verified empirically), and a dead
  run punishes the automation author for the model's habit -- so the one
  exec-viable channel is used instead:
- **PostToolUse** (both modes): after a captured run, one note pointing at
  the log; after an uncaptured violation (only reachable in exec, since
  interactive denies pre-execution), one corrective note with the tee'd
  re-run command. ``additionalContext`` is the documented PostToolUse
  channel and delivery is verified in both modes.

Dedupe: one seen-set per session (``<log_dir>/.notified-<session>``). A deny
pre-records its suggested paths so the compliant retry isn't re-taught;
capture notes fire once per log path; violation notes once per command.

Detection is narrow by design. A pipeline segment counts only when ALL hold:

- it STARTS with a recognized check: a bare tool from the ``tools`` list in
  ``[hooks.pre_tool_use.capture]`` (config owns that vocabulary -- extend it
  there, no code change) or a structural runner pattern
  (npm/pnpm/yarn/bun ``run <test|lint|typecheck|check|build>``, turbo,
  go test, cargo test/clippy/check, make <...test|check|lint>), allowing
  env-assignment and wrapper prefixes (npx/pnpm/uvx, flock/nice/timeout,
  command/exec/rtk/time);
- it pipes stdout through a top-level ``|`` or ``|&``;
- it does not already capture (``tee`` or a ``>``/``>>`` file redirect).

Everything else passes untouched: ``curl ... | bash`` (the pipe is the
payload), ``git log | rg``, bare check runs with no pipe, fireAndForget
(harness already logs to a file), and heredoc commands (bodies defeat the
pipe scanner).

Fail-open, mirroring rtk_rewrite.py: toggle via
``[hooks.pre_tool_use.capture]`` in configs/droid.toml; any internal error
exits cleanly and the original command runs.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import sys
from pathlib import Path

# add hooks dir to path for rel import
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils import (  # type: ignore
    HookInputError,
    PostToolUseInput,
    PreToolUseInput,
    exit,
    get_toml_section,
    load_toml,
    read_input,
)

HOOK_EVENT_PRE = "PreToolUse"
HOOK_EVENT_POST = "PostToolUse"

_SEGMENT_SEPARATORS = frozenset({"&&", "||", ";", "\n"})
_PIPE_TOKENS = frozenset({"|", "|&"})

# Wrappers that may precede the actual check: env assignments, generic
# command prefixes, flag/positional-taking niceness/locking wrappers (relies
# on regex backtracking to leave the check exposed), and pkg runners.
_PREFIX = (
    r"(?:[A-Za-z_][A-Za-z0-9_]*=\S+\s+)*"
    r"(?:(?:command|exec|rtk|time)\s+)*"
    r"(?:(?:flock|nice|ionice|timeout)(?:\s+\S+){1,3}\s+)?"
    r"(?:(?:npx|pnpm|yarn|bun|bunx|uvx|uv\s+run)\s+)?"
)

_RUNNERS = (
    r"(?:(?:npm|pnpm|yarn|bun)\s+(?:run\s+)?"
    r"(?:tests?(?::[\w-]+)?|lint|type-?checks?|checks?|build)\b"
    r"|turbo\s+run\s+[\w:.-]*(?:test|lint|typecheck|check|build)"
    r"|go\s+test\b"
    r"|cargo\s+(?:test|clippy|check)\b"
    # make targets must END in the keyword (optionally hyphen-suffixed) so
    # `make checklist`-style near-misses don't get blocked.
    r"|make\s+\S*(?:test|check|lint)s?(?:[-_][\w]+)*(?=\s|$))"
)

_TEE_RE = re.compile(r"\btee\b")
# `2>&1`, `>&2`, `&>` shuffle streams; they are not file capture.
_REDIRECT_NOISE_RE = re.compile(r"\d?>&\d?|&>")
_FILE_REDIRECT_RE = re.compile(r">")
_NON_SLUG_RE = re.compile(r"[^a-z0-9]+")
_SLUG_DROP_TOKENS = frozenset(
    {"flock", "nice", "ionice", "timeout", "command", "exec", "time"}
)

DEFAULT_LOG_DIR = "/tmp/droid-capture"

# `droid exec` sets these in the hook environment; interactive sessions do
# not. In exec, PreToolUse deny is fail-fast fatal and updatedInput is
# dropped, so enforcement moves to the PostToolUse note.
_EXEC_ENV_MARKERS = (
    "FACTORY_EXEC_TARGET_AUTONOMY",
    "FACTORY_DISABLE_SETTINGS_PERSISTENCE",
)


def _is_exec_session() -> bool:
    return any(marker in os.environ for marker in _EXEC_ENV_MARKERS)


def _validator_re(tools: list[str]) -> re.Pattern[str]:
    """Compile the segment-start matcher from the config-owned tools list."""
    escaped = sorted(
        (re.escape(tool) for tool in tools if tool.strip()),
        key=len,
        reverse=True,  # longest-first so prefixes never shadow longer names
    )
    tools_alt = f"(?:{'|'.join(escaped)})\\b|" if escaped else ""
    return re.compile(rf"^\s*{_PREFIX}(?:{tools_alt}{_RUNNERS})")


def _scan_top_level(command: str) -> list[tuple[int, str]]:
    """Positions of top-level shell operators, skipping quotes and subshells."""
    ops: list[tuple[int, str]] = []
    index = 0
    depth = 0
    quote: str | None = None
    while index < len(command):
        char = command[index]
        if quote is not None:
            if char == "\\" and quote in ('"', "`"):
                index += 2
                continue
            if char == quote:
                quote = None
            index += 1
            continue
        if char in ("'", '"', "`"):
            quote = char
        elif char == "\\":
            index += 2
            continue
        elif char == "(":
            depth += 1
        elif char == ")":
            depth = max(0, depth - 1)
        elif depth == 0 and char == "|":
            if command.startswith("||", index):
                ops.append((index, "||"))
                index += 1
            elif command.startswith("|&", index):
                ops.append((index, "|&"))
                index += 1
            else:
                ops.append((index, "|"))
        elif depth == 0 and command.startswith("&&", index):
            ops.append((index, "&&"))
            index += 1
        elif depth == 0 and char in ";\n":
            ops.append((index, char))
        index += 1
    return ops


def _blank_quoted(command: str) -> str:
    """Return ``command`` with quoted interiors replaced by spaces.

    Lets regexes match real shell syntax without being fooled by lookalike
    text inside quotes (e.g. a prompt string describing a tee'd command).
    """
    chars = list(command)
    index = 0
    quote: str | None = None
    while index < len(chars):
        char = chars[index]
        if quote is not None:
            if char == "\\" and quote in ('"', "`") and index + 1 < len(chars):
                chars[index] = chars[index + 1] = " "
                index += 2
                continue
            if char == quote:
                quote = None
            chars[index] = " "
            index += 1
            continue
        if char in ("'", '"', "`"):
            quote = char
        elif char == "\\" and index + 1 < len(chars):
            index += 1
        index += 1
    return "".join(chars)


def _capture_segment(
    command: str,
    seg_start: int,
    seg_end: int,
    pipes: list[tuple[int, str]],
    validator_re: re.Pattern[str],
    log_dir: str,
    name_suffix: str,
) -> tuple[int, str, str] | None:
    """Return (insert_pos, insert_text, log_path) if the segment needs a tee."""
    segment = command[seg_start:seg_end]
    match = validator_re.match(segment)
    if match is None:
        return None
    if _TEE_RE.search(segment):
        return None
    if _FILE_REDIRECT_RE.search(_REDIRECT_NOISE_RE.sub("", segment)):
        return None
    if not pipes:
        return None

    tokens = [
        token
        for token in match.group(0).split()
        if "=" not in token
        and "/" not in token
        and not token.startswith("-")
        and not token.isdigit()
        and token not in _SLUG_DROP_TOKENS
    ]
    slug = _NON_SLUG_RE.sub("-", "-".join(tokens[-3:]).lower()).strip("-")
    log_path = os.path.join(log_dir, f"{slug or 'check'}-{name_suffix}.log")
    pipe_pos, pipe_token = pipes[0]
    return pipe_pos + len(pipe_token), f" tee {log_path} |", log_path


def _rewrite(
    command: str,
    validator_re: re.Pattern[str],
    log_dir: str,
    session_id: str,
) -> tuple[str, list[str]]:
    """Insert ``tee <log>`` after the first pipe of each uncaptured check
    segment. Returns (corrected_command, log_paths); paths are a pure
    function of (command, session), so Pre and Post derive identical names."""
    ops = _scan_top_level(command)
    command_hash = hashlib.sha1(command.encode()).hexdigest()[:6]
    session_tag = session_id[:8] or "nosession"

    insertions: list[tuple[int, str, str]] = []
    seg_start = 0
    pipes: list[tuple[int, str]] = []
    for pos, token in [*ops, (len(command), ";")]:  # sentinel closes the tail
        if token in _PIPE_TOKENS:
            pipes.append((pos, token))
            continue
        if token in _SEGMENT_SEPARATORS:
            result = _capture_segment(
                command,
                seg_start,
                pos,
                pipes,
                validator_re,
                log_dir,
                f"{session_tag}-{command_hash}-{len(insertions)}",
            )
            if result is not None:
                insertions.append(result)
            seg_start = pos + len(token)
            pipes = []

    if not insertions:
        return command, []

    corrected = command
    for pos, text, _path in sorted(insertions, key=lambda item: item[0], reverse=True):
        corrected = corrected[:pos] + text + corrected[pos:]
    return corrected, [path for _pos, _text, path in insertions]


# ============================================================================
# Config + session state
# ============================================================================


def _load_config(config_path: str, event_name: str) -> dict[str, object]:
    if not config_path:
        return {}
    try:
        return load_toml(config_path)
    except OSError as exc:
        exit(
            1,
            text=f"[capture] config error: {exc}",
            to_stderr=True,
            hook_event_name=event_name,
        )
    except Exception as exc:
        exit(
            1,
            text=f"[capture] config parse error: {exc}",
            to_stderr=True,
            hook_event_name=event_name,
        )


def _parse_args(argv: list[str]) -> str:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--config-file", default="")
    return parser.parse_args(argv).config_file


def _load_capture_section(event_name: str) -> dict[str, object] | None:
    """Return the [hooks.pre_tool_use.capture] section, or None if disabled."""
    config = _load_config(_parse_args(sys.argv[1:]), event_name)
    section = get_toml_section(config, "hooks", "pre_tool_use", "capture")
    return None if section.get("enabled") is False else section


def _log_dir(section: dict[str, object]) -> str:
    log_dir = section.get("log_dir")
    return log_dir if isinstance(log_dir, str) and log_dir else DEFAULT_LOG_DIR


def _tools(section: dict[str, object]) -> list[str]:
    tools = section.get("tools")
    return [t for t in tools if isinstance(t, str)] if isinstance(tools, list) else []


def _seen_file(log_dir: str, session_id: str) -> str:
    return os.path.join(log_dir, f".notified-{session_id[:8] or 'nosession'}")


def _seen(log_dir: str, session_id: str) -> set[str]:
    try:
        with open(_seen_file(log_dir, session_id)) as handle:
            return set(handle.read().splitlines())
    except OSError:
        return set()


def _record(log_dir: str, session_id: str, entries: list[str]) -> None:
    try:
        os.makedirs(log_dir, mode=0o700, exist_ok=True)
        with open(_seen_file(log_dir, session_id), "a") as handle:
            handle.writelines(f"{entry}\n" for entry in entries)
    except OSError:
        pass  # dedupe state is best-effort; never lose the message over it


def _in_scope_command(tool_name: str, tool_input: dict[str, object]) -> str | None:
    """Return the command when this Execute call is in scope, else None."""
    if tool_name != "Execute":
        return None
    command = tool_input.get("command")
    if (
        not isinstance(command, str)
        or not command.strip()
        or tool_input.get("fireAndForget")
        or "<<" in command  # heredoc/herestring bodies defeat the pipe scanner
    ):
        return None
    return command


# ============================================================================
# Event handlers
# ============================================================================


def _handle_pre_tool_use(hook_input: PreToolUseInput) -> None:
    command = _in_scope_command(hook_input.tool_name, hook_input.tool_input)
    if command is None:
        exit(hook_event_name=HOOK_EVENT_PRE)

    section = _load_capture_section(HOOK_EVENT_PRE)
    if section is None:
        exit(hook_event_name=HOOK_EVENT_PRE)

    try:
        log_dir = _log_dir(section)
        corrected, log_paths = _rewrite(
            command, _validator_re(_tools(section)), log_dir, hook_input.session_id
        )
        if not log_paths or _is_exec_session():
            # Exec: deny is fail-fast fatal there; the PostToolUse note
            # carries the correction instead.
            exit(hook_event_name=HOOK_EVENT_PRE)
        # Pre-record so the compliant retry's PostToolUse note stays silent:
        # the deny reason below already teaches the path.
        _record(log_dir, hook_input.session_id, log_paths)
    except SystemExit:
        raise
    except Exception:
        exit(hook_event_name=HOOK_EVENT_PRE)  # fail open

    reason = (
        "[capture] Capture check output file-first BEFORE inline filtering. "
        "Re-run exactly as:\n\n"
        f"    {corrected}\n\n"
        "Afterwards query the log (rg/Read) instead of re-running the check "
        "to change filters. A pipeline's exit code is the last filter's, not "
        "the check's -- read pass/fail from the log's summary lines."
    )
    exit(decision="deny", reason=reason, hook_event_name=HOOK_EVENT_PRE)


def _post_context(
    command: str, section: dict[str, object], log_dir: str, session_id: str
) -> str | None:
    """Captured run -> point at the log. Uncaptured violation (reachable only
    in exec; interactive denies pre-execution) -> corrective note. One note
    per path / per command per session."""
    seen = _seen(log_dir, session_id)

    # Actual tee targets only -- quoted lookalike text (a prompt string
    # describing a tee'd command) and bare log-path mentions don't count.
    tee_paths = re.findall(
        rf"\btee\s+(?:-a\s+)?({re.escape(log_dir)}/\S+?\.log)\b",
        _blank_quoted(command),
    )
    if tee_paths:
        fresh = list(
            dict.fromkeys(p for p in tee_paths if os.path.isfile(p) and p not in seen)
        )
        if not fresh:
            return None
        _record(log_dir, session_id, fresh)
        return (
            f"[capture] Full check output: {', '.join(fresh)}. Query it with "
            "rg/Read instead of re-running the check; the pipeline's exit "
            "code was the last filter's, not the check's."
        )

    corrected, log_paths = _rewrite(
        command, _validator_re(_tools(section)), log_dir, session_id
    )
    if not log_paths:
        return None
    key = f"cmd:{hashlib.sha1(command.encode()).hexdigest()[:12]}"
    if key in seen:
        return None
    _record(log_dir, session_id, [key])
    return (
        "[capture] That check's full output was NOT captured -- only the "
        "filtered slice survives, and the exit code was the last filter's, "
        "not the check's. If anything was missed, re-run once as:\n\n"
        f"    {corrected}\n\n"
        "then query the log (rg/Read) instead of re-running again."
    )


def _handle_post_tool_use(hook_input: PostToolUseInput) -> None:
    command = _in_scope_command(hook_input.tool_name, hook_input.tool_input)
    if command is None:
        exit(hook_event_name=HOOK_EVENT_POST)

    section = _load_capture_section(HOOK_EVENT_POST)
    if section is None:
        exit(hook_event_name=HOOK_EVENT_POST)

    try:
        context = _post_context(
            command, section, _log_dir(section), hook_input.session_id
        )
    except SystemExit:
        raise
    except Exception:
        exit(hook_event_name=HOOK_EVENT_POST)  # fail open

    if context is None:
        exit(hook_event_name=HOOK_EVENT_POST)
    exit(
        output={
            "suppressOutput": True,
            "hookSpecificOutput": {
                "hookEventName": HOOK_EVENT_POST,
                "additionalContext": context,
            },
        },
        hook_event_name=HOOK_EVENT_POST,
    )


def main() -> None:
    try:
        hook_input = read_input()
    except HookInputError as exc:
        exit(1, text=f"[capture] input error: {exc}", to_stderr=True)

    if isinstance(hook_input, PreToolUseInput):
        _handle_pre_tool_use(hook_input)
    elif isinstance(hook_input, PostToolUseInput):
        _handle_post_tool_use(hook_input)
    exit()


if __name__ == "__main__":
    raise SystemExit(main())
