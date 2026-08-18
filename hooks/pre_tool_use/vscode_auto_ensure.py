#!/usr/bin/env python3
"""PreToolUse hook: transparently ensure the workspace for vscode:* MCP tools.

When a droid calls e.g. vscode:get_diagnostics with a workspace_path that has
no live bridge instance, this hook spawns the isolated headless editor on the
spot (via the vscode-workspace skill's manager), so the tool call just works.
An already-running workspace costs one in-process socket health check.

Failure policy: hook-infrastructure problems (missing script, unparsable
input, config errors) fail open and let the tool run. A completed but failed
`ensure` denies the call with the real reason — the tool would fail anyway,
and a clear reason beats a raw socket error.
"""

from __future__ import annotations

import argparse
import json
import os
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
from utils.vscode_workspace import (  # type: ignore
    MANAGER_SCRIPT,
    MANAGER_SCRIPTS_DIR,
    run_manager,
    warn,
)

HOOK_EVENT_NAME = "PreToolUse"
# Tools that operate on the socket directory globally and need no workspace.
GLOBAL_TOOLS = {"vscode:list_workspaces", "vscode:health_check"}


def _requested_files(tool_input: dict) -> list[str]:
    """Files the tool call is about to query — worth pre-opening on a cold
    spawn so the first result is populated instead of empty."""
    files = tool_input.get("__NOT_RECOMMEND__filePaths")
    if isinstance(files, list):
        return [f for f in files if isinstance(f, str) and f]
    single = tool_input.get("filePath")
    return [single] if isinstance(single, str) and single else []


def main() -> None:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--config-file", default="", help="Path to TOML config file")
    args = parser.parse_args(sys.argv[1:])

    try:
        hook_input = read_input_as(PreToolUseInput)
    except HookInputError:
        exit(hook_event_name=HOOK_EVENT_NAME)

    tool_name = hook_input.tool_name
    if not tool_name.startswith("vscode:") or tool_name in GLOBAL_TOOLS:
        exit(hook_event_name=HOOK_EVENT_NAME)

    raw_path = hook_input.tool_input.get("workspace_path")
    if not isinstance(raw_path, str):
        raw_path = ""
    # Default to the session's project dir so zero-arg vscode:* calls work.
    if not (raw_path or hook_input.cwd):
        exit(hook_event_name=HOOK_EVENT_NAME)  # let the tool report its own error
    requested = raw_path or hook_input.cwd

    # The bridge socket is md5(VSCode's canonical workspace path) while the
    # MCP server hashes the raw tool input — symlinks, "..", or a missing
    # resolve step would silently target a different (nonexistent) socket.
    resolved = str(Path(requested).expanduser().resolve())

    try:
        config_data = load_toml(args.config_file)
    except Exception as exc:
        warn("vscode_auto_ensure", f"config error, passing through: {exc}")
        exit(hook_event_name=HOOK_EVENT_NAME)

    config = get_toml_section(
        config_data, "hooks", "pre_tool_use", "vscode_auto_ensure"
    )
    if not bool(config.get("enabled", False)):
        exit(hook_event_name=HOOK_EVENT_NAME)

    if not MANAGER_SCRIPT.exists():
        warn("vscode_auto_ensure", f"manager script missing: {MANAGER_SCRIPT}")
        exit(hook_event_name=HOOK_EVENT_NAME)

    timeout = int(config.get("timeout", 90))
    session = os.environ.get("DROID_SESSION_ID") or hook_input.session_id or "unknown"

    def pass_through() -> None:
        """Proceed with the tool call, filling in or canonicalizing
        workspace_path when the droid omitted it or passed a non-canonical one."""
        if resolved != raw_path:
            exit(
                decision="allow",
                reason=f"[vscode_auto_ensure] workspace_path set to {resolved} "
                f"(defaulted to cwd or canonicalized)",
                updated_input={**hook_input.tool_input, "workspace_path": resolved},
            )
        exit(hook_event_name=HOOK_EVENT_NAME)

    # Warm path: import the manager in-process and reuse a healthy workspace
    # without paying for a second interpreter (~100-200ms saved per call).
    # Only the heavy spawn path justifies a subprocess.
    try:
        sys.path.insert(0, str(MANAGER_SCRIPTS_DIR))
        from ws_manager.core import ensure_fast  # type: ignore

        if ensure_fast(Path(resolved), session) is not None:
            pass_through()
    except Exception as exc:
        warn(
            "vscode_auto_ensure", f"fast path error, falling back to full ensure: {exc}"
        )

    command = [
        "ensure",
        resolved,
        "--session",
        session,
        "--timeout",
        str(timeout),
    ]
    if bool(config.get("warm", True)):
        for file in _requested_files(hook_input.tool_input):
            command += ["--warm", file]
        command += ["--warm-wait", str(float(config.get("warm_wait", 4)))]
    else:
        command.append("--no-warm-git")

    try:
        result = run_manager(*command, timeout=timeout + 30)
    except Exception as exc:
        exit(
            decision="deny",
            reason=f"[vscode_auto_ensure] failed to run workspace ensure for "
            f"{resolved}: {exc}",
        )

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        payload = {}

    if result.returncode != 0 or payload.get("status") == "error":
        reason = payload.get("error") or result.stderr.strip() or "unknown error"
        exit(
            decision="deny",
            reason=f"[vscode_auto_ensure] could not start a VSCode workspace at "
            f"{resolved}: {reason}",
        )

    pass_through()


if __name__ == "__main__":
    main()
