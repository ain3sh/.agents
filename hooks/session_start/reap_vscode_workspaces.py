#!/usr/bin/env python3
"""SessionStart hook: reap vscode workspaces idle beyond the configured window.

Catches workspaces orphaned by hard-crashed sessions (whose SessionEnd hook
never ran). `last_seen` is refreshed by every ensure — including the
transparent ones from the pre_tool_use auto-ensure hook — so only workspaces
no session has touched within the window are retired. Fails open.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# add hooks dir to path for rel import
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils import (  # type: ignore
    HookInputError,
    SessionStartInput,
    exit,
    get_toml_section,
    load_toml,
    read_input_as,
)
from utils.vscode_workspace import MANAGER_SCRIPT, run_manager, warn  # type: ignore

HOOK_EVENT_NAME = "SessionStart"


def main() -> None:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--config-file", default="", help="Path to TOML config file")
    args = parser.parse_args(sys.argv[1:])

    try:
        config_data = load_toml(args.config_file)
    except Exception as exc:
        warn("reap_vscode_workspaces", f"config error, skipping: {exc}")
        exit(hook_event_name=HOOK_EVENT_NAME)

    config = get_toml_section(
        config_data, "hooks", "session_start", "vscode_workspaces"
    )
    if not bool(config.get("enabled", False)):
        exit(hook_event_name=HOOK_EVENT_NAME)

    try:
        hook_input = read_input_as(SessionStartInput)
    except HookInputError as exc:
        warn("reap_vscode_workspaces", f"hook input error, skipping: {exc}")
        exit(hook_event_name=HOOK_EVENT_NAME)

    when = config.get("when", ["startup"])
    if isinstance(when, list) and hook_input.source not in when:
        exit(hook_event_name=HOOK_EVENT_NAME)

    if not MANAGER_SCRIPT.exists():
        warn("reap_vscode_workspaces", f"manager script missing: {MANAGER_SCRIPT}")
        exit(hook_event_name=HOOK_EVENT_NAME)

    try:
        result = run_manager(
            "reap",
            "--idle-hours",
            str(float(config.get("idle_hours", 12))),
            timeout=int(config.get("timeout", 30)),
        )
        if result.returncode != 0:
            warn(
                "reap_vscode_workspaces",
                f"reap failed: {result.stderr.strip() or result.stdout.strip()}",
            )
    except Exception as exc:
        warn("reap_vscode_workspaces", f"reap error: {exc}")

    exit(hook_event_name=HOOK_EVENT_NAME)


if __name__ == "__main__":
    main()
