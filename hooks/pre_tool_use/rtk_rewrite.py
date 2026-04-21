#!/usr/bin/env python3
"""PreToolUse hook: rewrite Execute commands through rtk for token savings.

Transparent and fail-open by design:

- Only acts on ``Execute`` tool calls.
- Skips commands that already start with ``rtk `` (idempotent).
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


def _extract_surface(rewritten: str) -> str | None:
    """Pull the rtk surface name (token after 'rtk') from a rewrite string."""
    try:
        parts = shlex.split(rewritten)
    except ValueError:
        return None
    return parts[1] if len(parts) >= 2 and parts[0] == "rtk" else None


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
