"""State layout, path hashing, and the workspace registry.

A "workspace" in vscode-mcp terms is a running VSCode window whose MCP Bridge
extension listens on a per-workspace unix socket named
vscode-mcp-<md5(abspath)[:8]>.sock in SOCKET_DIR (owned by the extension).
Our own state lives under STATE_ROOT: per-workspace instance profiles, the
shared extensions dir, the registry, and logs.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATE_ROOT = Path(
    os.environ.get("VSCODE_WS_HOME", "~/.local/share/vscode-mcp-agent")
).expanduser()
EXTENSIONS_DIR = STATE_ROOT / "extensions"
INSTANCES_DIR = STATE_ROOT / "instances"
REGISTRY_DIR = STATE_ROOT / "registry"
LOGS_DIR = STATE_ROOT / "logs"

SOCKET_DIR = (
    Path(os.environ.get("XDG_DATA_HOME", "~/.local/share")).expanduser()
    / "yutengjing-vscode-mcp"
)

BRIDGE_EXTENSION = "YuTengjing.vscode-mcp-bridge"
# Safety marker: we only ever signal processes whose cmdline contains this
# string, so a recycled PID can never cause collateral damage.
SAFETY_MARKER = "vscode-mcp-agent"


def hash_path(path: Path) -> str:
    return hashlib.md5(str(path).encode()).hexdigest()[:8]


def socket_path_for(ws_hash: str) -> Path:
    return SOCKET_DIR / f"vscode-mcp-{ws_hash}.sock"


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _registry_file(ws_hash: str) -> Path:
    return REGISTRY_DIR / f"{ws_hash}.json"


def load_entry(ws_hash: str) -> dict[str, Any] | None:
    try:
        return json.loads(_registry_file(ws_hash).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def write_entry(ws_hash: str, entry: dict[str, Any]) -> None:
    REGISTRY_DIR.mkdir(parents=True, exist_ok=True)
    tmp = _registry_file(ws_hash).with_suffix(".tmp")
    tmp.write_text(json.dumps(entry, indent=2) + "\n", encoding="utf-8")
    tmp.replace(_registry_file(ws_hash))


def remove_entry(ws_hash: str) -> None:
    _registry_file(ws_hash).unlink(missing_ok=True)


def all_entries() -> list[dict[str, Any]]:
    if not REGISTRY_DIR.is_dir():
        return []
    entries = []
    for file in sorted(REGISTRY_DIR.glob("*.json")):
        try:
            entries.append(json.loads(file.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError):
            continue
    return entries
