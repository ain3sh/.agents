"""Command logic: setup, ensure, retire, reap, list.

Retirement is graceful first: save dirty editors, then ask the window to
close itself over the bridge socket (workbench.action.closeWindow), which
lets the extension's deactivate() remove its own socket file. A verified
process-group kill is the fallback, followed by a stale-socket unlink.
"""

from __future__ import annotations

import argparse
import json
import re
import socket
import subprocess
import time
import tomllib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .procs import (
    hard_kill,
    pid_alive_and_ours,
    spawn,
    sweep_instance_processes,
    sweep_orphan_language_servers,
)
from .rpc import WsError, health, rpc
from .state import (
    BRIDGE_EXTENSION,
    EXTENSIONS_DIR,
    INSTANCES_DIR,
    LOGS_DIR,
    REGISTRY_DIR,
    SOCKET_DIR,
    STATE_ROOT,
    all_entries,
    hash_path,
    load_entry,
    now,
    remove_entry,
    socket_path_for,
    write_entry,
)


def _config_extensions(config_file: str) -> list[str]:
    """Default extension ids from [tools.vscode-workspace] in the TOML config."""
    try:
        data = tomllib.loads(Path(config_file).expanduser().read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return []
    value = data.get("tools", {}).get("vscode-workspace", {}).get("extensions", [])
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item]


def _pinned_server_version(mcp_config: str) -> str | None:
    """The version pinned in the vscode MCP server's npx arg, if any.

    Upstream releases the server and the bridge extension in lockstep under
    one version tag, so the pin in mcp.json is the single source of truth for
    both sides. Returns None for @latest / unpinned configs.
    """
    try:
        data = json.loads(Path(mcp_config).expanduser().read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    args = data.get("mcpServers", {}).get("vscode", {}).get("args", [])
    if not isinstance(args, list):
        return None
    for arg in args:
        match = re.search(r"@vscode-mcp/vscode-mcp-server@(\S+)", str(arg))
        if match:
            version = match.group(1).strip("'\"")
            return None if version == "latest" else version
    return None


def cmd_setup(args: argparse.Namespace) -> dict[str, Any]:
    """One-time install: state dirs + extensions into the shared dir.

    The bridge extension is installed at the exact version the MCP server is
    pinned to in mcp.json, so the two protocol sides can never drift apart.
    """
    code = args.code
    for directory in (EXTENSIONS_DIR, INSTANCES_DIR, REGISTRY_DIR, LOGS_DIR):
        directory.mkdir(parents=True, exist_ok=True)

    bridge_version = _pinned_server_version(args.mcp_config)
    bridge = (
        f"{BRIDGE_EXTENSION}@{bridge_version}" if bridge_version else BRIDGE_EXTENSION
    )

    wanted = [bridge, *_config_extensions(args.config_file), *args.extensions]
    wanted = list(dict.fromkeys(wanted))  # dedupe, keep order
    installed: list[str] = []
    skipped: list[str] = []
    for ext in wanted:
        ext_id, _, ext_version = ext.partition("@")
        # With a version pin only the exact match counts as present; a
        # different installed version is replaced below.
        present = EXTENSIONS_DIR / (
            f"{ext_id.lower()}-{ext_version}" if ext_version else ""
        )
        if not args.force and (
            (ext_version and present.is_dir())
            or (not ext_version and list(EXTENSIONS_DIR.glob(ext_id.lower() + "-*")))
        ):
            skipped.append(ext)
            continue
        if ext_version:
            subprocess.run(
                [
                    code,
                    f"--user-data-dir={STATE_ROOT / 'bootstrap'}",
                    f"--extensions-dir={EXTENSIONS_DIR}",
                    "--uninstall-extension",
                    ext_id,
                ],
                capture_output=True,
                timeout=120,
            )  # best-effort: clears any mismatched version
        subprocess.run(
            [
                code,
                f"--user-data-dir={STATE_ROOT / 'bootstrap'}",
                f"--extensions-dir={EXTENSIONS_DIR}",
                "--install-extension",
                ext,
            ],
            check=True,
            capture_output=True,
            timeout=300,
        )
        installed.append(ext)

    return {
        "status": "ok",
        "state_root": str(STATE_ROOT),
        "bridge_version": bridge_version or "unpinned",
        "installed": installed,
        "already_present": skipped,
    }


def ensure_fast(path: Path, session: str) -> dict[str, Any] | None:
    """Reuse path: if a healthy bridge already serves `path`, refresh the
    registry (session claim + last_seen) and return the payload; else None.

    Shared by cmd_ensure and the pre_tool_use auto-ensure hook, which imports
    this module in-process to keep warm vscode:* tool calls single-process.
    """
    ws_hash = hash_path(path)
    sock = socket_path_for(ws_hash)
    live = health(sock)
    if live is None:
        return None
    entry = load_entry(ws_hash) or {}
    sessions = list(entry.get("sessions") or [])
    if session not in sessions:
        sessions.append(session)
    entry.update(
        {
            "hash": ws_hash,
            "workspace_path": str(path),
            "sessions": sessions,
            "last_seen": now(),
        }
    )
    entry.setdefault("pid", None)
    entry.setdefault("mode", "external")
    write_entry(ws_hash, entry)
    return {
        "status": "reused",
        "workspace_path": str(path),
        "socket_path": str(sock),
        "health": live,
    }


def _git_modified_files(path: Path, cap: int = 20) -> list[str]:
    """Files git reports as modified (staged or not) or untracked — the same
    set the bridge's getDiagnostics targets when called with an empty file
    list. Empty for non-git workspaces."""
    files: list[str] = []
    for command in (
        ["git", "-C", str(path), "diff", "--name-only", "-z", "HEAD"],
        ["git", "-C", str(path), "ls-files", "--others", "--exclude-standard", "-z"],
    ):
        try:
            result = subprocess.run(command, capture_output=True, timeout=10)
        except (OSError, subprocess.SubprocessError):
            return []
        if result.returncode != 0:
            return []
        files.extend(
            entry
            for entry in result.stdout.decode(errors="replace").split("\0")
            if entry
        )
    return files[:cap]


def _warm_up(sock: Path, files: list[str], wait: float) -> list[str]:
    """Pre-open files on a fresh instance so language servers start analyzing
    before the first real query arrives. Best-effort: returns the files that
    opened successfully."""
    if not files:
        return []
    try:
        result = rpc(
            sock,
            "openFiles",
            {"files": [{"filePath": f, "showEditor": True} for f in files]},
            timeout=15,
        )
    except (WsError, OSError, socket.timeout):
        return []
    opened = [
        str(item["filePath"])
        for item in (result or {}).get("results", [])
        if isinstance(item, dict) and item.get("success")
    ]
    if opened and wait > 0:
        time.sleep(wait)
    return opened


def cmd_ensure(args: argparse.Namespace) -> dict[str, Any]:
    path = Path(args.path).expanduser().resolve()
    if path.is_file():
        raise WsError(
            f"workspace_path must be a directory, got a file: {path} — "
            f"pass its project directory (e.g. {path.parent})"
        )
    if not path.is_dir():
        raise WsError(f"not a directory: {path}")
    ws_hash = hash_path(path)
    sock = socket_path_for(ws_hash)

    # Fast path: a healthy bridge already serves this workspace.
    reused = ensure_fast(path, args.session)
    if reused is not None:
        return reused

    # Stale socket or half-alive instance from a crashed run: clean first.
    sock.unlink(missing_ok=True)
    old = load_entry(ws_hash)
    if old:
        hard_kill(old)
        remove_entry(ws_hash)

    proc = spawn(path, ws_hash, headless=not args.no_headless, code=args.code)

    deadline = time.monotonic() + args.timeout
    while time.monotonic() < deadline:
        live = health(sock)
        if live is not None:
            # Give the workbench a moment to finish initializing: a file opened
            # while the window is still coming up can leave its language
            # server permanently unaware of that document.
            if args.settle > 0:
                time.sleep(args.settle)
            # Explicit warm list wins; otherwise warm the git-modified set so
            # a cold get_diagnostics (empty filePaths) comes back populated.
            warm_files = args.warm or (
                _git_modified_files(path) if args.warm_git else []
            )
            warmed = _warm_up(sock, warm_files, args.warm_wait)
            entry = {
                "hash": ws_hash,
                "workspace_path": str(path),
                "sessions": [args.session],
                "spawned_at": now(),
                "last_seen": now(),
                "pid": proc.pid,
                "mode": "headless" if not args.no_headless else "window",
            }
            write_entry(ws_hash, entry)
            return {
                "status": "spawned",
                "workspace_path": str(path),
                "socket_path": str(sock),
                "pid": proc.pid,
                "warmed": warmed,
                "health": live,
            }
        if proc.poll() is not None:
            tail = log_tail(ws_hash)
            raise WsError(
                f"editor exited during startup (code {proc.returncode}); "
                f"log tail: {tail}"
            )
        time.sleep(0.5)

    hard_kill({"hash": ws_hash, "pid": proc.pid})
    raise WsError(
        f"workspace did not become ready within {args.timeout}s; "
        f"log tail: {log_tail(ws_hash)}"
    )


def cmd_retire(args: argparse.Namespace) -> dict[str, Any]:
    path = Path(args.path).expanduser().resolve()
    ws_hash = hash_path(path)
    outcome = _retire_hash(ws_hash, timeout=args.timeout)
    return {"status": "retired", "workspace_path": str(path), **outcome}


def _retire_hash(ws_hash: str, timeout: float = 20.0) -> dict[str, Any]:
    entry = load_entry(ws_hash) or {"hash": ws_hash}
    sock = socket_path_for(ws_hash)
    graceful = False
    killed = False

    if health(sock) is not None:
        try:
            # Save dirty editors first so the close below cannot block on a
            # save prompt (nobody is watching a headless window).
            rpc(
                sock,
                "executeCommand",
                {"command": "workbench.action.files.saveAll", "saveAllEditors": False},
            )
            rpc(
                sock,
                "executeCommand",
                {"command": "workbench.action.closeWindow", "saveAllEditors": False},
            )
        except (WsError, OSError, socket.timeout):
            pass  # fall through to liveness wait / hard kill

        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if not sock.exists() and not pid_alive_and_ours(entry.get("pid"), ws_hash):
                graceful = True
                break
            time.sleep(0.5)

    swept: list[int] = []
    if not graceful:
        killed = hard_kill(entry)
    else:
        # A graceful window close leaves detached helpers behind (crashpad).
        swept = sweep_instance_processes(ws_hash)

    # Language servers outlive their window either way; a dead
    # --clientProcessId proves the owning extension host is gone.
    swept += sweep_orphan_language_servers()

    sock.unlink(missing_ok=True)  # no-op if deactivate() already removed it
    remove_entry(ws_hash)
    return {
        "hash": ws_hash,
        "graceful": graceful,
        "force_killed": killed,
        "swept_helpers": swept,
    }


def _idle_seconds(entry: dict[str, Any]) -> float | None:
    last_seen = entry.get("last_seen") or entry.get("spawned_at")
    if not isinstance(last_seen, str):
        return None
    try:
        seen = datetime.fromisoformat(last_seen)
    except ValueError:
        return None
    return (datetime.now(timezone.utc) - seen).total_seconds()


def cmd_reap(args: argparse.Namespace) -> dict[str, Any]:
    retired: list[str] = []
    reaped: list[str] = []
    kept: list[str] = []
    released: list[str] = []

    for entry in all_entries():
        ws_hash = str(entry.get("hash", ""))
        sock = socket_path_for(ws_hash)
        alive = pid_alive_and_ours(entry.get("pid"), ws_hash)
        healthy = health(sock) is not None

        sessions = list(entry.get("sessions") or [])
        if args.all:
            _retire_hash(ws_hash)
            retired.append(ws_hash)
        elif args.session and args.session in sessions:
            # Refcounted ownership: only retire when the last owner leaves.
            sessions.remove(args.session)
            if sessions:
                entry["sessions"] = sessions
                write_entry(ws_hash, entry)
                released.append(ws_hash)
            else:
                _retire_hash(ws_hash)
                retired.append(ws_hash)
        elif not alive and not healthy:
            # Owner is gone and the bridge is dead: pure zombie cleanup.
            hard_kill(entry)
            sock.unlink(missing_ok=True)
            remove_entry(ws_hash)
            reaped.append(ws_hash)
        elif (
            args.idle_hours is not None
            and healthy
            and (_idle_seconds(entry) or 0) > args.idle_hours * 3600
        ):
            # Stale despite healthy: no session has touched it within the
            # idle window (last_seen is refreshed by every ensure).
            _retire_hash(ws_hash)
            retired.append(ws_hash)
        else:
            # NOTE: last_seen is deliberately NOT refreshed here — it is the
            # idle signal for --idle-hours and must only move on real use
            # (ensure), not on reaper sweeps.
            kept.append(ws_hash)

    # Orphan sockets with no registry entry: only remove provably dead ones.
    orphans_removed: list[str] = []
    if SOCKET_DIR.is_dir():
        known = {str(e.get("hash")) for e in all_entries()}
        for sock in sorted(SOCKET_DIR.glob("vscode-mcp-*.sock")):
            ws_hash = sock.stem.removeprefix("vscode-mcp-")
            if ws_hash in known:
                continue
            if health(sock) is None:
                sock.unlink(missing_ok=True)
                orphans_removed.append(ws_hash)

    # Language servers whose extension host died, whatever workspace they
    # served (crash recovery, missed retire, ...).
    orphans_swept = sweep_orphan_language_servers()

    return {
        "status": "ok",
        "retired": retired,
        "released": released,
        "reaped": reaped,
        "kept": kept,
        "orphan_sockets_removed": orphans_removed,
        "orphan_language_servers_swept": orphans_swept,
    }


def cmd_list(_args: argparse.Namespace) -> dict[str, Any]:
    workspaces = []
    for entry in all_entries():
        ws_hash = str(entry.get("hash", ""))
        sock = socket_path_for(ws_hash)
        workspaces.append(
            {
                **entry,
                "socket_path": str(sock),
                "process_alive": pid_alive_and_ours(entry.get("pid"), ws_hash),
                "healthy": health(sock) is not None,
            }
        )
    sockets = (
        sorted(str(p) for p in SOCKET_DIR.glob("vscode-mcp-*.sock"))
        if SOCKET_DIR.is_dir()
        else []
    )
    return {"status": "ok", "workspaces": workspaces, "sockets": sockets}


def log_tail(ws_hash: str, lines: int = 20, max_bytes: int = 64_000) -> str:
    """Last `lines` of the instance log, reading at most `max_bytes` from the
    end instead of the whole file."""
    try:
        with (LOGS_DIR / f"{ws_hash}.log").open("rb") as handle:
            handle.seek(0, 2)
            size = handle.tell()
            handle.seek(max(0, size - max_bytes))
            content = handle.read().decode(encoding="utf-8", errors="replace")
    except OSError:
        return "<no log>"
    tail = content.strip().splitlines()[-lines:]
    return " | ".join(tail) if tail else "<empty log>"
