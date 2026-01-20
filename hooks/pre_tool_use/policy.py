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
from utils import (  # type: ignore
    HookInputError,
    PreToolUseInput,
    emit,
    exit,
    get_toml_section,
    load_toml,
    read_input_as,
)


# ============================================================================
# Configuration
# ============================================================================

Decision = str


@dataclass(slots=True, frozen=True)
class Override:
    decision: Decision | None
    message: str | None


@dataclass(slots=True, frozen=True)
class Config:
    trust: tuple[str, ...]
    verify: tuple[str, ...]
    block: tuple[str, ...]
    allow_message: str | None
    ask_message: str | None
    deny_message: str | None
    default_decision: Decision
    overrides: tuple[tuple[str, Override], ...]


def _parse_args(argv: list[str]) -> Config:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--config-file", default="", help="Path to TOML config file")
    parser.add_argument("--trust", action="append", default=[])
    parser.add_argument("--verify", action="append", default=[])
    parser.add_argument("--block", action="append", default=[])
    args = parser.parse_args(argv)

    try:
        config_data = load_toml(args.config_file)
    except OSError as exc:
        exit(1, text=f"[policy] Config file error: {exc}", to_stderr=True)
    except Exception as exc:
        exit(1, text=f"[policy] Config parse error: {exc}", to_stderr=True)

    policy_root = _policy_root(config_data)
    allow_section = _policy_section(config_data, "allow")
    ask_section = _policy_section(config_data, "ask")
    deny_section = _policy_section(config_data, "deny")

    trust = _split_targets(args.trust) or _split_targets(_list_from_config(allow_section.get("tools")))
    verify = _split_targets(args.verify) or _split_targets(_list_from_config(ask_section.get("tools")))
    block = _split_targets(args.block) or _split_targets(_list_from_config(deny_section.get("tools")))

    default_decision = policy_root.get("default_decision")
    if default_decision not in {"system", "allow", "ask", "deny"}:
        default_decision = "system"

    overrides = _parse_overrides(_policy_section(config_data, "overrides"))

    return Config(
        trust=trust,
        verify=verify,
        block=block,
        allow_message=_as_str(allow_section.get("message")),
        ask_message=_as_str(ask_section.get("message")),
        deny_message=_as_str(deny_section.get("message")),
        default_decision=str(default_decision),
        overrides=overrides,
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


def _as_str(value: object) -> str | None:
    return value if isinstance(value, str) else None


def _list_from_config(value: object) -> list[str]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return []


def _policy_root(data: dict[str, object]) -> dict[str, object]:
    return get_toml_section(data, "hooks", "pre_tool_use", "policy")


def _policy_section(data: dict[str, object], name: str) -> dict[str, object]:
    return get_toml_section(data, "hooks", "pre_tool_use", "policy", name)


def _parse_overrides(section: dict[str, object]) -> tuple[tuple[str, Override], ...]:
    overrides: list[tuple[str, Override]] = []
    for key, value in section.items():
        if not isinstance(key, str):
            continue
        if not isinstance(value, dict):
            continue
        decision = value.get("decision")
        message = value.get("message")
        override = Override(
            decision=decision if decision in {"system", "allow", "ask", "deny"} else None,
            message=message if isinstance(message, str) else None,
        )
        overrides.append((key, override))
    return tuple(overrides)


def _match_mcp_server(server: str, pattern: str) -> bool:
    """Match MCP server name with flexible pattern matching.

    Supports:
    - Exact match: "vscode" matches "vscode"
    - Glob patterns: "code*" matches "codebase"
    - Partial/contains: "codebase" matches "plugin_codebase_codebase"
    """
    if pattern == "*":
        return True
    # Try exact fnmatch first (handles globs)
    if fnmatch.fnmatch(server, pattern):
        return True
    # Fall back to substring match for flexibility with prefixed server names
    # e.g., pattern "codebase" matches server "plugin_codebase_codebase"
    return pattern in server


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
            if _match_mcp_server(server, server_pattern) and fnmatch.fnmatch(tool, tool_pattern):
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

def _match_override(tool_name: str, overrides: tuple[tuple[str, Override], ...]) -> Override | None:
    for pattern, override in overrides:
        if _match_any((pattern,), tool_name):
            return override
    return None


def _render_message(message: str | None, tool_name: str) -> str | None:
    if not message:
        return None
    try:
        return message.format(tool_name=tool_name)
    except Exception:
        return message

def _decide(tool_name: str, config: Config) -> Decision:
    if _match_any(config.block, tool_name):
        return "deny"
    if _match_any(config.verify, tool_name):
        return "ask"
    if _match_any(config.trust, tool_name):
        return "allow"
    return config.default_decision


def _handle_pre_tool_use(hook_input: PreToolUseInput, config: Config) -> None:
    tool_name = hook_input.tool_name
    base_decision = _decide(tool_name, config)
    override = _match_override(tool_name, config.overrides)

    decision = override.decision if override and override.decision else base_decision
    reason = None
    if override and override.message:
        reason = _render_message(override.message, tool_name)
    elif decision == "deny":
        reason = _render_message(config.deny_message, tool_name)
    elif decision == "ask":
        reason = _render_message(config.ask_message, tool_name)
    elif decision == "allow":
        reason = _render_message(config.allow_message, tool_name)

    if decision == "system":
        exit()

    if decision == "deny":
        emit(decision="deny", reason=reason or f"[policy] {tool_name} blocked by tool policy")
        return

    if decision == "ask":
        emit(decision="ask", reason=reason or f"[policy] confirm {tool_name} tool use")
        return

    if decision == "allow":
        _emit_allow(reason=reason)
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
