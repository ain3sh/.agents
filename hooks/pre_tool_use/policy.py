#!/usr/bin/env python3
"""PreToolUse hook to auto-manage tool permissions."""
from __future__ import annotations
import argparse
import re
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

@dataclass(slots=True, frozen=True)
class Override:
    decision: str | None
    message: str | None
@dataclass(slots=True, frozen=True)
class Config:
    allow: tuple[str, ...]
    ask: tuple[str, ...]
    deny: tuple[str, ...]
    allow_message: str | None
    ask_message: str | None
    deny_message: str | None
    overrides: tuple[tuple[str, Override], ...]


def _parse_tools(value: object) -> tuple[str, ...]:
    if not value:
        return ()
    if isinstance(value, str):
        entries = (value,)
    elif isinstance(value, list):
        entries = tuple(v for v in value if isinstance(v, str))
        if not entries:
            return ()
    else:
        return ()

    parts = (part.strip() for entry in entries for part in entry.split(","))
    return tuple(p for p in parts if p)

def _parse_overrides(section: object) -> tuple[tuple[str, Override], ...]:
    valid = {"allow", "ask", "deny"}
    if not isinstance(section, dict):
        return ()

    overrides: list[tuple[str, Override]] = []
    for pattern, raw in section.items():
        if not isinstance(pattern, str) or not isinstance(raw, dict):
            continue

        decision = raw.get("decision")
        message = raw.get("message")
        overrides.append(
            (
                pattern,
                Override(
                    decision=decision if isinstance(decision, str) and decision in valid else None,
                    message=message if isinstance(message, str) else None,
                ),
            )
        )
    return tuple(overrides)

def _parse_args(argv: list[str]) -> Config:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--config-file", default="", help="Path to TOML config file")
    for name in ("allow", "ask", "deny"):
        parser.add_argument(f"--{name}", action="append", default=[])
    args = parser.parse_args(argv)
    config_data = {}
    if args.config_file:
        try:
            config_data = load_toml(args.config_file)
        except OSError as exc:
            exit(1, text=f"[policy] Config file error: {exc}", to_stderr=True)
        except Exception as exc:
            exit(1, text=f"[policy] Config parse error: {exc}", to_stderr=True)

    base_path = ("hooks", "pre_tool_use", "policy")
    sections = {k: get_toml_section(config_data, *base_path, k) for k in ("allow", "ask", "deny")}
    overrides_section = get_toml_section(config_data, *base_path, "overrides")

    tools_from_config = {k: _parse_tools(sections[k].get("tools")) for k in ("allow", "ask", "deny")}
    tools_from_cli = {k: _parse_tools(getattr(args, k)) for k in ("allow", "ask", "deny")}
    tools = {k: tools_from_config[k] + tools_from_cli[k] for k in ("allow", "ask", "deny")}

    def _msg(section: dict[str, object]) -> str:
        m = section.get("message")
        return m if isinstance(m, str) else ""

    return Config(
        allow=tools["allow"],
        ask=tools["ask"],
        deny=tools["deny"],
        allow_message=_msg(sections["allow"]),
        ask_message=_msg(sections["ask"]),
        deny_message=_msg(sections["deny"]),
        overrides=_parse_overrides(overrides_section),
    )


# ============================================================================
# Main hook logic
# ============================================================================

def _match_tool(tool_name: str, pattern: str) -> bool:
    p = pattern.strip()
    if not p:
        return False

    if ":" not in p: # fallback: glob on full tool name
        return fnmatch.fnmatch(tool_name, p)

    # parse `server:tool` pattern with wildcard defaults for empty sides
    server_pattern, tool_pattern = (x or "*" for x in p.split(":", 1))

    # parse MCP-style tool name: split on 2+ underscores
    parts = re.split(r"_{2,}", tool_name.strip(), maxsplit=2)
    if parts and parts[0] == "mcp": # strip optional leading `mcp`
        parts = parts[1:]
    if len(parts) < 2 or not all(parts):
        return False
    server, tool = parts[0], parts[-1]

    # server match: wildcard, glob, or substring (flexible server naming)
    if server_pattern != "*" and not (fnmatch.fnmatch(server, server_pattern) or server_pattern in server):
        return False

    # tool match: glob on the tool portion
    return fnmatch.fnmatch(tool, tool_pattern)

def _handle_pre_tool_use(hook_input: PreToolUseInput, config: Config) -> None:
    tool_name = hook_input.tool_name
    override = next(
        (ov for pat, ov in config.overrides if _match_tool(tool_name, pat)),
        None,
    )
    base_decision = next(
        (
            decision
            for decision, targets in (
                ("deny", config.deny),
                ("ask", config.ask),
                ("allow", config.allow),
            )
            if any(_match_tool(tool_name, t) for t in targets)
        ),
        None,
    )
    decision = override.decision\
        if (override and override.decision)\
        else base_decision

    if decision is None:  # defer to system by default
        exit()

    template = (
        override.message
        if (override and override.message)
        else getattr(config, f"{decision}_message") or ""
    )
    emit(decision=decision, reason=template.format(tool_name=tool_name))


def main() -> int:
    try:
        hook_input = read_input_as(PreToolUseInput)
    except HookInputError as exc:
        exit(1, text=f"[policy] Hook input error: {exc}", to_stderr=True)

    _handle_pre_tool_use(hook_input, _parse_args(sys.argv[1:]))
    exit()

if __name__ == "__main__":
    raise SystemExit(main())