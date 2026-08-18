"""Shared plumbing for the vscode-workspace hooks.

The feature itself lives in `skills/vscode-workspace` (manager + SKILL.md);
this module only gives the per-event hook scripts one canonical way to
locate and invoke the manager. Used by:
- hooks/pre_tool_use/vscode_auto_ensure.py
- hooks/session_start/reap_vscode_workspaces.py
- hooks/session_end/retire_vscode_workspaces.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

MANAGER_SCRIPTS_DIR = (
    Path(__file__).resolve().parents[2] / "skills" / "vscode-workspace" / "scripts"
)
MANAGER_SCRIPT = MANAGER_SCRIPTS_DIR / "vscode_ws.py"


def warn(tag: str, message: str) -> None:
    print(f"[{tag}] {message}", file=sys.stderr)


def run_manager(*argv: str, timeout: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(MANAGER_SCRIPT), *argv],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
