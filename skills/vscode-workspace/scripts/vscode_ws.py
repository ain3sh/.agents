#!/usr/bin/env python3
"""vscode-ws: CLI for the on-demand VSCode MCP workspace manager.

Creates isolated headless VSCode instances whose MCP Bridge extension serves
live LSP data over a per-workspace unix socket, and retires them without
leaving zombie processes or sockets. All logic lives in the ws_manager
package next to this file; this is only the argparse front end.

Subcommands: setup, ensure, retire, reap, list. All print JSON to stdout.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ws_manager import core  # noqa: E402
from ws_manager.rpc import WsError  # noqa: E402


def emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(prog="vscode-ws", description=__doc__)
    parser.add_argument("--code", default="code", help="editor binary (default: code)")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("setup", help="install state dirs + bridge extension")
    p.add_argument("extensions", nargs="*", help="extra extension ids to install")
    p.add_argument("--force", action="store_true", help="reinstall even if present")
    p.add_argument(
        "--config-file",
        default="~/.agents/configs/droid.toml",
        help="TOML config whose [tools.vscode-workspace] extensions are installed too",
    )
    p.add_argument(
        "--mcp-config",
        default="~/.factory/mcp.json",
        help="MCP config whose pinned vscode server version drives the bridge "
        "extension version",
    )
    p.set_defaults(func=core.cmd_setup)

    p = sub.add_parser("ensure", help="create or reuse a workspace")
    p.add_argument("path", help="absolute workspace directory")
    p.add_argument(
        "--session",
        default=os.environ.get("DROID_SESSION_ID", "unknown"),
        help="owning droid session id (default: $DROID_SESSION_ID or 'unknown')",
    )
    p.add_argument("--timeout", type=float, default=90.0)
    p.add_argument(
        "--settle",
        type=float,
        default=3.0,
        help="seconds to wait after the bridge answers before reporting a fresh "
        "spawn as ready (lets the workbench finish initializing; 0 disables)",
    )
    p.add_argument(
        "--warm",
        action="append",
        default=[],
        help="file to pre-open on a fresh spawn so language servers start "
        "analyzing before the first query (repeatable)",
    )
    p.add_argument(
        "--warm-wait",
        type=float,
        default=4.0,
        help="seconds to wait after warming files (0 disables)",
    )
    p.add_argument(
        "--warm-git",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="with no explicit --warm files, pre-open git-modified files (default: on)",
    )
    p.add_argument(
        "--no-headless",
        action="store_true",
        help="show the window on the desktop instead of running headless",
    )
    p.set_defaults(func=core.cmd_ensure)

    p = sub.add_parser("retire", help="gracefully close + clean up a workspace")
    p.add_argument("path", help="absolute workspace directory")
    p.add_argument("--timeout", type=float, default=20.0)
    p.set_defaults(func=core.cmd_retire)

    p = sub.add_parser("reap", help="clean zombies; optionally retire by owner")
    p.add_argument(
        "--session",
        default="",
        help="release this session's claim; retire workspaces it solely owned",
    )
    p.add_argument("--all", action="store_true", help="retire every workspace")
    p.add_argument(
        "--idle-hours",
        type=float,
        default=None,
        help="also retire healthy workspaces unused (no ensure) for this long",
    )
    p.set_defaults(func=core.cmd_reap)

    p = sub.add_parser("list", help="show registry, liveness, and sockets")
    p.set_defaults(func=core.cmd_list)

    args = parser.parse_args()
    try:
        emit(args.func(args))
    except (WsError, subprocess.CalledProcessError, OSError) as exc:
        emit({"status": "error", "error": str(exc)})
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
