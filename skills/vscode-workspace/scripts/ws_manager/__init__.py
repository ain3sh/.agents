"""Lifecycle manager for on-demand headless VSCode MCP workspaces.

Module ownership:
- state: state root layout, path hashing, socket paths, registry CRUD
- rpc: bridge socket protocol (newline-delimited JSON over unix sockets)
- procs: process lifecycle (spawn, verify, kill, zombie sweeps)
- core: command logic (setup / ensure / retire / reap / list)
"""

from . import core, procs, rpc, state

__all__ = ["core", "procs", "rpc", "state"]
