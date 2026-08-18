"""Bridge socket protocol: newline-delimited JSON RPC over unix sockets.

One request per connection; the bridge answers with a matching `id` and
either a `result` or an `error` object. Mirrors the framing of the upstream
@vscode-mcp/vscode-mcp-ipc EventDispatcher.
"""

from __future__ import annotations

import json
import socket
import time
from pathlib import Path
from typing import Any


class WsError(Exception):
    pass


def rpc(sock: Path, method: str, params: dict[str, Any], timeout: float = 10.0) -> Any:
    request_id = f"vscode-ws-{time.time_ns()}"
    request = {"id": request_id, "method": method, "params": params}
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.settimeout(timeout)
        client.connect(str(sock))
        client.sendall((json.dumps(request) + "\n").encode())
        buffer = b""
        while True:
            chunk = client.recv(65536)
            if not chunk:
                break
            buffer += chunk
            while b"\n" in buffer:
                line, buffer = buffer.split(b"\n", 1)
                line = line.strip()
                if not line:
                    continue
                response = json.loads(line)
                if response.get("id") != request_id:
                    continue
                if "error" in response:
                    raise WsError(f"{method}: {response['error']}")
                return response.get("result")
    raise WsError(f"{method}: connection closed without a response")


def health(sock: Path, timeout: float = 3.0) -> dict[str, Any] | None:
    """The bridge's health result, or None when the socket is dead/absent."""
    if not sock.exists():
        return None
    try:
        result = rpc(sock, "health", {}, timeout=timeout)
    except (WsError, OSError, json.JSONDecodeError, socket.timeout):
        return None
    return result if isinstance(result, dict) else None
