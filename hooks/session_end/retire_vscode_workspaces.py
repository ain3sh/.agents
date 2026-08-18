#!/usr/bin/env python3
"""SessionEnd hook to retire vscode-mcp workspaces owned by the ending session.

Runs `vscode_ws.py reap --session <id>` (or `--all`) so headless VSCode
instances spawned via the vscode-workspace skill are closed gracefully and
zombie processes/sockets are cleaned. Ownership is refcounted: a workspace
shared with another live session survives. Fails open: any error is reported
on stderr and the hook exits cleanly without blocking session teardown.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# add hooks dir to path for rel import
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils import (  # type: ignore
    HookInputError,
    SessionEndInput,
    exit,
    get_toml_section,
    load_toml,
    read_input_as,
)
from utils.vscode_workspace import MANAGER_SCRIPT, run_manager, warn  # type: ignore

HOOK_EVENT_NAME = "SessionEnd"


def main() -> None:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--config-file", default="", help="Path to TOML config file")
    args = parser.parse_args(sys.argv[1:])

    try:
        config_data = load_toml(args.config_file)
    except Exception as exc:
        warn("retire_vscode_workspaces", f"config error, skipping: {exc}")
        exit(hook_event_name=HOOK_EVENT_NAME)

    config = get_toml_section(config_data, "hooks", "session_end", "vscode_workspaces")
    if not bool(config.get("enabled", False)):
        exit(hook_event_name=HOOK_EVENT_NAME)

    try:
        hook_input = read_input_as(SessionEndInput)
    except HookInputError as exc:
        warn("retire_vscode_workspaces", f"hook input error, skipping: {exc}")
        exit(hook_event_name=HOOK_EVENT_NAME)

    if not MANAGER_SCRIPT.exists():
        warn("retire_vscode_workspaces", f"manager script missing: {MANAGER_SCRIPT}")
        exit(hook_event_name=HOOK_EVENT_NAME)

    argv: list[str] = ["reap"]
    if str(config.get("mode", "session")) == "all":
        argv.append("--all")
    else:
        argv += ["--session", hook_input.session_id]

    try:
        result = run_manager(*argv, timeout=int(config.get("timeout", 25)))
        if result.returncode != 0:
            warn(
                "retire_vscode_workspaces",
                f"reap failed: {result.stderr.strip() or result.stdout.strip()}",
            )
    except Exception as exc:
        warn("retire_vscode_workspaces", f"reap error: {exc}")

    exit(hook_event_name=HOOK_EVENT_NAME)


if __name__ == "__main__":
    main()
