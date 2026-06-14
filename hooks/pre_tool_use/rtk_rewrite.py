#!/usr/bin/env python3
"""PreToolUse hook: rewrite Execute commands through rtk for token savings.

Transparent and fail-open by design:

- Only acts on ``Execute`` tool calls.
- Skips commands that already start with ``rtk `` (idempotent).
- Skips ``git push`` commands because wrapping network writes adds latency with
  little token-saving upside.
- Consults ``rtk rewrite``; if rtk is absent, slow, or the command has no
  compressed form, the hook exits cleanly and the original command runs.
- Per-surface toggles live under ``[hooks.pre_tool_use.rtk.surfaces]`` in
  ``~/.agents/configs/droid.toml`` — disable a single surface (e.g. ``git``)
  without killing the whole hook.

The hook emits only ``hookSpecificOutput.updatedInput`` (no
``permissionDecision``), so downstream PreToolUse hooks (policy,
commit_review_guard, etc.) still run on the rewritten command.
"""

from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from pathlib import Path

# add hooks dir to path for rel import
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils import (  # type: ignore
    HookInputError,
    PreToolUseInput,
    exit,
    get_toml_section,
    load_toml,
    read_input_as,
)

HOOK_EVENT_NAME = "PreToolUse"

# `rtk rewrite` exits 0 (docs) or 3 (observed v0.37.x) on successful rewrite,
# 1 when the command has no compressed form. Accept both success codes.
RTK_REWRITE_EXIT_OK = frozenset({0, 3})
RTK_TIMEOUT_SEC = 5

SHELL_SEPARATORS = frozenset({"&&", "||", ";", "|", "|&"})
COMMAND_PREFIXES = frozenset({"command", "exec", "nohup", "time"})
GIT_GLOBAL_OPTIONS_WITH_VALUE = frozenset(
    {
        "-C",
        "-c",
        "--config-env",
        "--exec-path",
        "--git-dir",
        "--namespace",
        "--super-prefix",
        "--work-tree",
    }
)
GIT_GLOBAL_OPTIONS_WITH_INLINE_VALUE = tuple(
    f"{option}=" for option in GIT_GLOBAL_OPTIONS_WITH_VALUE if option.startswith("--")
)
WRAPPER_OPTIONS_WITH_VALUE = frozenset(
    {
        "-C",
        "-g",
        "-h",
        "-p",
        "-T",
        "-t",
        "-u",
        "--chdir",
        "--close-from",
        "--command-timeout",
        "--group",
        "--host",
        "--prompt",
        "--role",
        "--type",
        "--unset",
        "--user",
    }
)
WRAPPER_OPTIONS_WITH_INLINE_VALUE = tuple(
    f"{option}=" for option in WRAPPER_OPTIONS_WITH_VALUE if option.startswith("--")
)


def _extract_surface(rewritten: str) -> str | None:
    """Pull the rtk surface name (token after 'rtk') from a rewrite string."""
    try:
        parts = shlex.split(rewritten)
    except ValueError:
        return None
    return parts[1] if len(parts) >= 2 and parts[0] == "rtk" else None


def _git_subcommand_at(tokens: list[str], git_index: int) -> str | None:
    index = git_index + 1
    while index < len(tokens):
        token = tokens[index]
        if token in SHELL_SEPARATORS:
            return None
        if token in GIT_GLOBAL_OPTIONS_WITH_VALUE:
            index += 2
            continue
        if token.startswith(GIT_GLOBAL_OPTIONS_WITH_INLINE_VALUE):
            index += 1
            continue
        if token.startswith("-"):
            index += 1
            continue
        return token
    return None


def _is_shell_assignment(token: str) -> bool:
    name, separator, _value = token.partition("=")
    if not separator or not name or name[0].isdigit():
        return False
    return all(character.isalnum() or character == "_" for character in name)


def _skip_wrapper_options(tokens: list[str], index: int) -> int:
    while index < len(tokens) and tokens[index].startswith("-"):
        token = tokens[index]
        if token in WRAPPER_OPTIONS_WITH_VALUE:
            index += 2
        elif token.startswith(WRAPPER_OPTIONS_WITH_INLINE_VALUE):
            index += 1
        else:
            index += 1
    return index


def _git_index_in_segment(tokens: list[str]) -> int | None:
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if _is_shell_assignment(token):
            index += 1
            continue
        if token == "env":
            index = _skip_wrapper_options(tokens, index + 1)
            continue
        if token == "sudo":
            index = _skip_wrapper_options(tokens, index + 1)
            continue
        if token in COMMAND_PREFIXES:
            index += 1
            continue
        return index if token == "git" else None
    return None


def _is_git_push_command(command: str) -> bool:
    try:
        tokens = shlex.split(command)
    except ValueError:
        return False

    segment: list[str] = []
    for token in [*tokens, ";"]:
        if token not in SHELL_SEPARATORS:
            segment.append(token)
            continue

        git_index = _git_index_in_segment(segment)
        if git_index is not None and _git_subcommand_at(segment, git_index) == "push":
            return True
        segment.clear()
    return False


def _rtk_rewrite(command: str) -> tuple[str, str | None]:
    """Ask ``rtk rewrite`` for a compressed form of ``command``.

    Returns ``(rewritten_cmd, surface)`` on success, ``(command, None)`` when
    rtk has no rewrite or is unavailable. Never raises.
    """
    try:
        result = subprocess.run(
            ["rtk", "rewrite", command],
            capture_output=True,
            text=True,
            timeout=RTK_TIMEOUT_SEC,
            check=False,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return command, None

    if result.returncode not in RTK_REWRITE_EXIT_OK:
        return command, None

    rewritten = result.stdout.strip()
    if not rewritten or rewritten == command:
        return command, None

    surface = _extract_surface(rewritten)
    return rewritten, surface


def _load_config(config_path: str) -> dict[str, object]:
    if not config_path:
        return {}
    try:
        return load_toml(config_path)
    except OSError as exc:
        exit(
            1,
            text=f"[rtk] config error: {exc}",
            to_stderr=True,
            hook_event_name=HOOK_EVENT_NAME,
        )
    except Exception as exc:
        exit(
            1,
            text=f"[rtk] config parse error: {exc}",
            to_stderr=True,
            hook_event_name=HOOK_EVENT_NAME,
        )


def _is_surface_enabled(config: dict[str, object], surface: str) -> bool:
    """Per-surface on/off toggle.

    Config layout under ``[hooks.pre_tool_use.rtk]``::

        enabled = true            # master switch; default on

        [hooks.pre_tool_use.rtk.surfaces]
        git = false               # disable only git rewrites
        # any absent key defaults to enabled
    """
    section = get_toml_section(config, "hooks", "pre_tool_use", "rtk")
    if section.get("enabled") is False:
        return False
    surfaces = get_toml_section(config, "hooks", "pre_tool_use", "rtk", "surfaces")
    return surfaces.get(surface) is not False  # default-on; explicit False disables


def _parse_args(argv: list[str]) -> str:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--config-file", default="")
    return parser.parse_args(argv).config_file


def main() -> None:
    try:
        hook_input = read_input_as(PreToolUseInput)
    except HookInputError as exc:
        exit(
            1,
            text=f"[rtk] input error: {exc}",
            to_stderr=True,
            hook_event_name=HOOK_EVENT_NAME,
        )

    if hook_input.tool_name != "Execute":
        exit(hook_event_name=HOOK_EVENT_NAME)

    command = hook_input.tool_input.get("command")
    if (
        not isinstance(command, str)
        or not command.strip()
        or command.lstrip().startswith("rtk ")
        or _is_git_push_command(command)
    ):
        exit(hook_event_name=HOOK_EVENT_NAME)

    rewritten, surface = _rtk_rewrite(command)
    if surface is None or rewritten == command:
        exit(hook_event_name=HOOK_EVENT_NAME)

    config = _load_config(_parse_args(sys.argv[1:]))
    if not _is_surface_enabled(config, surface):
        exit(hook_event_name=HOOK_EVENT_NAME)

    new_input = {**hook_input.tool_input, "command": rewritten}
    exit(
        output={
            "hookSpecificOutput": {
                "hookEventName": HOOK_EVENT_NAME,
                "updatedInput": new_input,
            },
            "suppressOutput": True,
        },
        hook_event_name=HOOK_EVENT_NAME,
    )


if __name__ == "__main__":
    raise SystemExit(main())
