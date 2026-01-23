#!/usr/bin/env python3
"""PostToolUse hook to inject instructions based on tool-specific rules.

This hook selects prompt files from TOML rules keyed by tool name and optional
input/output matchers, then adds the combined instructions as context.

Trigger: PostToolUse (settings.json matcher should be "*")
Output: Adds additional context via hookSpecificOutput
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import cast

# add hooks dir to path for rel import
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils import (  # type: ignore
    HookInputError,
    HookOutput,
    PostToolUseInput,
    PostToolUseOutput,
    exit,
    get_project_dir,
    get_toml_section,
    load_toml,
    read_input_as,
)
from utils.instructions import (  # type: ignore
    build_template_context,
    dedupe,
    parse_str_list,
    render_instructions,
)


# ============================================================================
# Configuration
# ============================================================================

@dataclass(slots=True, frozen=True)
class Matchers:
    tool: str
    input_pattern: str | None
    output_pattern: str | None


@dataclass(slots=True, frozen=True)
class Rule:
    matchers: Matchers
    include: tuple[str, ...]
    include_text: tuple[str, ...]


@dataclass(slots=True, frozen=True)
class Config:
    prompts_dir: Path
    rules: tuple[Rule, ...]
    debug: bool


def _parse_matchers(value: object) -> Matchers | None:
    if not isinstance(value, dict):
        return None
    value_dict = cast(dict[str, object], value)
    tool = value_dict.get("tool")
    if not isinstance(tool, str) or not tool:
        tool = "*"
    input_pattern = value_dict.get("input")
    output_pattern = value_dict.get("output")
    return Matchers(
        tool=tool,
        input_pattern=input_pattern if isinstance(input_pattern, str) and input_pattern else None,
        output_pattern=output_pattern if isinstance(output_pattern, str) and output_pattern else None,
    )


def _parse_rules(value: object) -> tuple[Rule, ...]:
    if not isinstance(value, list):
        return ()

    rules: list[Rule] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        item_dict = cast(dict[str, object], item)
        include = parse_str_list(item_dict.get("include"))
        include_text = parse_str_list(item_dict.get("include_text"))
        if not include and not include_text:
            continue
        matchers = _parse_matchers(item_dict.get("match"))
        if matchers is None:
            matchers = Matchers(tool="*", input_pattern=None, output_pattern=None)
        rules.append(Rule(matchers=matchers, include=include, include_text=include_text))
    return tuple(rules)


def _parse_args(argv: list[str]) -> Config:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--config-file", default="", help="Path to TOML config file")
    parser.add_argument("--prompts-dir", default="", help="Base directory for instruction files")
    args = parser.parse_args(argv)

    try:
        config_data = load_toml(args.config_file)
    except OSError as exc:
        exit(
            1,
            text=f"[post_tool_use] Config file error: {exc}",
            to_stderr=True,
            hook_event_name="PostToolUse",
        )
    except Exception as exc:
        exit(
            1,
            text=f"[post_tool_use] Config parse error: {exc}",
            to_stderr=True,
            hook_event_name="PostToolUse",
        )

    config = get_toml_section(config_data, "hooks", "post_tool_use", "instructions")
    config_prompts = config.get("prompts_dir")
    if args.prompts_dir:
        prompts_dir_value = args.prompts_dir
    elif isinstance(config_prompts, str) and config_prompts:
        prompts_dir_value = config_prompts
    else:
        prompts_dir_value = "~/.agents/prompts"

    rules = _parse_rules(config.get("rules"))
    debug = bool(config.get("debug"))

    prompts_dir = Path(prompts_dir_value).expanduser()
    if not prompts_dir.is_absolute():
        project_dir = get_project_dir()
        if project_dir is not None:
            prompts_dir = project_dir / prompts_dir

    return Config(prompts_dir=prompts_dir, rules=rules, debug=debug)


# ============================================================================
# Matching helpers
# ============================================================================

def _match_tool(tool_name: str, pattern: str) -> bool:
    if not pattern or pattern == "*":
        return True
    if pattern.startswith("re:"):
        try:
            return re.search(pattern[3:], tool_name) is not None
        except re.error:
            return False
    return fnmatch.fnmatch(tool_name, pattern)


def _match_text(pattern: str | None, value: object) -> bool:
    if not pattern:
        return True
    text = json.dumps(value, ensure_ascii=False, sort_keys=True)
    if pattern.startswith("re:"):
        try:
            return re.search(pattern[3:], text) is not None
        except re.error:
            return False
    return pattern in text


# ============================================================================
# Content loading
# ============================================================================

def _resolve_includes(config: Config, hook_input: PostToolUseInput) -> tuple[tuple[str, ...], tuple[str, ...]]:
    if not config.rules:
        return (), ()

    ordered: list[str] = []
    text_blocks: list[str] = []
    for rule in config.rules:
        if not _match_tool(hook_input.tool_name, rule.matchers.tool):
            continue
        if not _match_text(rule.matchers.input_pattern, hook_input.tool_input):
            continue
        if not _match_text(rule.matchers.output_pattern, hook_input.tool_response):
            continue
        ordered.extend(rule.include)
        text_blocks.extend(rule.include_text)

    return dedupe(ordered), tuple(text_blocks)


# ============================================================================
# Main Hook Logic
# ============================================================================

def handle_post_tool_use(hook_input: PostToolUseInput, config: Config) -> str | None:
    include_files, include_text = _resolve_includes(config, hook_input)
    if not include_files and not include_text:
        return None
    content, missing, ambiguous = render_instructions(
        config.prompts_dir,
        include_files,
        include_text,
        build_template_context(hook_input),
    )
    if missing or ambiguous:
        warning_parts: list[str] = []
        if missing:
            warning_parts.append(f"missing={sorted(missing)}")
        if ambiguous:
            warning_parts.append(f"ambiguous={sorted(ambiguous)}")
        print(f"[post_tool_use] Unresolved placeholders: {', '.join(warning_parts)}", file=sys.stderr)
    return content


def _emit_debug(hook_input: PostToolUseInput, enabled: bool) -> None:
    if not enabled:
        return
    print(
        json.dumps(
            asdict(hook_input),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        file=sys.stderr,
    )


def main() -> None:
    config = _parse_args(sys.argv[1:])

    try:
        hook_input = read_input_as(PostToolUseInput)
    except HookInputError as exc:
        exit(
            1,
            text=f"[post_tool_use] Hook input error: {exc}",
            to_stderr=True,
            hook_event_name="PostToolUse",
        )

    _emit_debug(hook_input, config.debug)

    content = handle_post_tool_use(hook_input, config)
    if content:
        exit(
            output=HookOutput(
                hook_specific_output=PostToolUseOutput(additional_context=content)
            ),
            hook_event_name="PostToolUse",
        )
    exit(hook_event_name="PostToolUse")


if __name__ == "__main__":
    raise SystemExit(main())
