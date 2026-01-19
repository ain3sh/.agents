#!/usr/bin/env python3
"""PreToolUse hook to manage tool permissions and reduce MCP prompts."""
from __future__ import annotations

import argparse
import fnmatch
import sys
from dataclasses import dataclass
from pathlib import Path

# add hooks dir to path for rel import
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils import HookInputError, PreToolUseInput, emit, exit, read_input_as  # type: ignore


# ============================================================================
# Configuration
# ============================================================================

Decision = str


@dataclass(slots=True, frozen=True)
class Config:
    trust: tuple[str, ...]
    verify: tuple[str, ...]
    block: tuple[str, ...]


def _parse_args(argv: list[str]) -> Config:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--trust", action="append", default=[])
    parser.add_argument("--verify", action="append", default=[])
    parser.add_argument("--block", action="append", default=[])
    args = parser.parse_args(argv)

    trust = _split_targets(args.trust)
    verify = _split_targets(args.verify)
    block = _split_targets(args.block)

    return Config(
        trust=trust,
        verify=verify,
        block=block,
    )


def _split_targets(values: list[str]) -> tuple[str, ...]:
    if not values:
        return ()
    items: list[str] = []
    for value in values:
        for part in value.split(","):
            cleaned = part.strip()
            if cleaned:
                items.append(cleaned)
    return tuple(items)


def _match_any(targets: tuple[str, ...], tool_name: str) -> bool:
    for raw in targets:
        cleaned = raw.strip()
        if cleaned.startswith("mcp:"):
            rest = cleaned[4:]
            if "/" in rest:
                server_pattern, tool_pattern = rest.split("/", 1)
                server_pattern = server_pattern or "*"
                tool_pattern = tool_pattern or "*"
            else:
                server_pattern = rest or "*"
                tool_pattern = "*"

            if not tool_name.startswith("mcp__"):
                continue
            parts = tool_name.split("__", 2)
            if len(parts) < 3:
                continue
            server, tool = parts[1], parts[2]
            if fnmatch.fnmatch(server, server_pattern) and fnmatch.fnmatch(tool, tool_pattern):
                return True
            continue

        pattern = cleaned or "*"
        if fnmatch.fnmatch(tool_name, pattern):
            return True
    return False


# ============================================================================
# Output helpers
# ============================================================================

def _emit_allow(updated_input: dict[str, object] | None = None, reason: str | None = None) -> None:
    if updated_input is None:
        emit(decision="allow", reason=reason, suppress=True)
        return
    emit(decision="allow", reason=reason, suppress=True, updated_input=updated_input)


# ============================================================================
# Main hook logic
# ============================================================================

def _decide(tool_name: str, config: Config) -> Decision:
    if _match_any(config.block, tool_name):
        return "deny"
    if _match_any(config.verify, tool_name):
        return "ask"
    if _match_any(config.trust, tool_name):
        return "allow"
    return "system"


def _handle_pre_tool_use(hook_input: PreToolUseInput, config: Config) -> None:
    tool_name = hook_input.tool_name
    decision = _decide(tool_name, config)

    if decision == "system":
        exit()

    if decision == "deny":
        emit(decision="deny", reason=f"[policy] {tool_name} blocked by tool policy")
        return

    if decision == "ask":
        emit(decision="ask", reason=f"[policy] confirm {tool_name} tool use")
        return

    if decision == "allow":
        _emit_allow()
        return

    exit()


def main() -> int:
    config = _parse_args(sys.argv[1:])

    try:
        hook_input = read_input_as(PreToolUseInput)
    except HookInputError as exc:
        exit(1, text=f"[policy] Hook input error: {exc}", to_stderr=True)

    _handle_pre_tool_use(hook_input, config)
    exit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
