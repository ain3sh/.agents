"""Process lifecycle: spawn, verify, kill, and sweep.

Isolation model:
- per-workspace --user-data-dir (instances/<hash>/): own process tree, so a
  hard kill can never touch another workspace or a personal editor
- shared --extensions-dir (extensions/): the bridge extension is installed
  once by setup and reused read-only by every instance
- headless by default via `--ozone-platform=headless`: Electron runs without
  any display server. It must be a CLI arg, not an env var: code's cli.js
  strips DISPLAY/ELECTRON_*/XDG_* when spawning the GUI process (which is why
  xvfb-run's DISPLAY never arrives and windows leak onto the physical
  Wayland session), while argv passes through untouched. `code --wait` keeps
  the CLI process alive for the window's lifetime, so the spawned process
  group tracks the workspace exactly and killpg() tears everything down.
"""

from __future__ import annotations

import json
import os
import re
import signal
import subprocess
import time
from pathlib import Path
from typing import Any

from .state import EXTENSIONS_DIR, INSTANCES_DIR, LOGS_DIR, SAFETY_MARKER

# Instance profile defaults. The trust toggle is load-bearing: a fresh
# --user-data-dir opens folders in Restricted Mode, which disables semantic
# language servers (no TS type errors). Seeded before every spawn; our values
# win over whatever accumulated in the instance profile.
INSTANCE_SETTINGS = {
    "security.workspace.trust.enabled": False,
    "workbench.startupEditor": "none",
    "telemetry.telemetryLevel": "off",
    "extensions.autoUpdate": False,
    "update.mode": "none",
}


def seed_instance_settings(ws_hash: str) -> None:
    settings_path = INSTANCES_DIR / ws_hash / "User" / "settings.json"
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    existing: dict[str, Any] = {}
    try:
        existing = json.loads(settings_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        pass
    settings_path.write_text(
        json.dumps({**existing, **INSTANCE_SETTINGS}, indent=2) + "\n",
        encoding="utf-8",
    )


def spawn(
    path: Path, ws_hash: str, headless: bool, code: str
) -> subprocess.Popen[bytes]:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    seed_instance_settings(ws_hash)
    # Truncate per spawn: a fresh instance starts a fresh log, so logs stay
    # bounded to one launch's output instead of growing without limit.
    log_file = open(LOGS_DIR / f"{ws_hash}.log", "wb")  # noqa: SIM115
    command = [
        code,
        "--wait",
        "--new-window",
        f"--user-data-dir={INSTANCES_DIR / ws_hash}",
        f"--extensions-dir={EXTENSIONS_DIR}",
        "--skip-add-to-recently-opened",
        "--disable-gpu",
    ]
    if headless:
        command.append("--ozone-platform=headless")
    command.append(str(path))
    return subprocess.Popen(  # noqa: S603
        command,
        stdout=log_file,
        stderr=log_file,
        stdin=subprocess.DEVNULL,
        start_new_session=True,
    )


def _cmdline(pid: int) -> str:
    try:
        raw = Path(f"/proc/{pid}/cmdline").read_bytes()
    except OSError:
        return ""
    return raw.replace(b"\0", b" ").decode(errors="replace")


def pid_alive_and_ours(pid: object, ws_hash: str) -> bool:
    """True only if the pid exists and its cmdline proves it is ours."""
    if not isinstance(pid, int) or pid <= 0:
        return False
    cmdline = _cmdline(pid)
    return SAFETY_MARKER in cmdline and ws_hash in cmdline


def sweep_instance_processes(ws_hash: str) -> list[int]:
    """SIGTERM then SIGKILL any process whose cmdline references this instance.

    Catches detached survivors the process-group kill misses — e.g. Electron's
    crashpad handler, which reparents to init and outlives a closed window.
    Matching on the instance path keeps the sweep precise per workspace.
    """
    marker = str(INSTANCES_DIR / ws_hash)
    targets: list[int] = []
    for proc in Path("/proc").iterdir():
        if not proc.name.isdigit():
            continue
        pid = int(proc.name)
        if pid == os.getpid():
            continue
        if marker in _cmdline(pid):
            targets.append(pid)

    for pid in targets:
        try:
            os.kill(pid, signal.SIGTERM)
        except (ProcessLookupError, PermissionError):
            pass
    deadline = time.monotonic() + 2.0
    while time.monotonic() < deadline:
        survivors = [pid for pid in targets if marker in _cmdline(pid)]
        if not survivors:
            return targets
        time.sleep(0.2)
    for pid in survivors:
        try:
            os.kill(pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
    return targets


def sweep_orphan_language_servers() -> list[int]:
    """Kill language servers from the shared extensions dir whose owning
    extension host is dead.

    Language servers (eslintServer.js, pylance, gopls, ...) are spawned by the
    extension host with `--clientProcessId=<exthost-pid>` and can outlive a
    closed window. Their cmdlines point at the *shared* extensions dir, so
    they are indistinguishable per workspace — but a dead clientProcessId
    proves the owner is gone regardless of which workspace it served. PID
    reuse can only make a dead owner look alive (we skip, safe direction).
    """
    marker = str(EXTENSIONS_DIR)
    killed: list[int] = []
    for proc in Path("/proc").iterdir():
        if not proc.name.isdigit():
            continue
        pid = int(proc.name)
        if pid == os.getpid():
            continue
        cmdline = _cmdline(pid)
        if marker not in cmdline:
            continue
        match = re.search(r"--clientProcessId=(\d+)", cmdline)
        if not match:
            continue
        owner = int(match.group(1))
        try:
            os.kill(owner, 0)  # alive → belongs to a live workspace, skip
            continue
        except ProcessLookupError:
            pass
        except PermissionError:
            continue
        try:
            os.kill(pid, signal.SIGTERM)
            killed.append(pid)
        except (ProcessLookupError, PermissionError):
            pass
    return killed


def hard_kill(entry: dict[str, Any]) -> bool:
    """Kill the instance's process tree. Returns True if something was killed.

    Spawning used start_new_session=True, so pgid == pid. We verify the
    leader's cmdline against SAFETY_MARKER before signalling to guard
    against PID reuse, then sweep detached stragglers (crashpad) by cmdline.
    """
    ws_hash = str(entry.get("hash", ""))
    pid = entry.get("pid")
    killed = False
    if pid_alive_and_ours(pid, ws_hash):
        pgid = int(pid)
        for sig, grace in ((signal.SIGTERM, 3.0), (signal.SIGKILL, 1.0)):
            try:
                os.killpg(pgid, sig)
            except (ProcessLookupError, PermissionError):
                break
            deadline = time.monotonic() + grace
            while time.monotonic() < deadline:
                if not pid_alive_and_ours(pgid, ws_hash):
                    break
                time.sleep(0.2)
            if not pid_alive_and_ours(pgid, ws_hash):
                break
        killed = True
    swept = sweep_instance_processes(ws_hash)
    return killed or bool(swept)
