#!/usr/bin/env python3
"""SessionStart hook to inject default instructions from a base directory."""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import cast

# add hooks dir to path for rel import
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils import (  # type: ignore
    HookInputError,
    HookOutput,
    SessionStartInput,
    SessionStartOutput,
    exit,
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

HOOK_EVENT_NAME = "SessionStart"


@dataclass(slots=True, frozen=True)
class Rule:
    when: set[str]
    include: tuple[str, ...]
    include_text: tuple[str, ...]


@dataclass(slots=True, frozen=True)
class Config:
    prompts_dir: Path
    rules: tuple[Rule, ...]


def _parse_when(value: object) -> set[str]:
    if isinstance(value, list):
        return {item for item in value if isinstance(item, str) and item}
    if isinstance(value, str):
        return {item for item in (part.strip() for part in value.split(",")) if item}
    return set()


def _parse_rules(value: object) -> tuple[Rule, ...]:
    if not isinstance(value, list):
        return ()

    rules: list[Rule] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        item_dict = cast(dict[str, object], item)
        when = _parse_when(item_dict.get("when"))
        include = parse_str_list(item_dict.get("include"))
        include_text = parse_str_list(item_dict.get("include_text"))
        if not include and not include_text:
            continue
        rules.append(Rule(when=when, include=include, include_text=include_text))
    return tuple(rules)


def _parse_args(argv: list[str]) -> Config:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--config-file", default="", help="Path to TOML config file")
    parser.add_argument(
        "--prompts-dir",
        default="",
        help="Base directory for instruction files",
    )
    args = parser.parse_args(argv)

    try:
        config_data = load_toml(args.config_file)
    except OSError as exc:
        exit(
            1,
            text=f"[session_start] Config file error: {exc}",
            to_stderr=True,
            hook_event_name=HOOK_EVENT_NAME,
        )
    except Exception as exc:
        exit(
            1,
            text=f"[session_start] Config parse error: {exc}",
            to_stderr=True,
            hook_event_name=HOOK_EVENT_NAME,
        )

    config = get_toml_section(config_data, "hooks", "session_start", "instructions")
    config_prompts = config.get("prompts_dir")
    if args.prompts_dir:
        prompts_dir_value = args.prompts_dir
    elif isinstance(config_prompts, str) and config_prompts:
        prompts_dir_value = config_prompts
    else:
        prompts_dir_value = "~/.agents/prompts"

    rules = _parse_rules(config.get("rules"))

    return Config(
        prompts_dir=Path(prompts_dir_value).expanduser(),
        rules=rules,
    )


def _matches_source(when: set[str], source: str) -> bool:
    if not when:
        return True
    if "*" in when:
        return True
    return source in when

def _resolve_includes(config: Config, source: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    if not config.rules:
        return (), ()

    ordered: list[str] = []
    text_blocks: list[str] = []
    for rule in config.rules:
        if _matches_source(rule.when, source):
            ordered.extend(rule.include)
            text_blocks.extend(rule.include_text)
    return dedupe(ordered), tuple(text_blocks)


def main():
    config = _parse_args(sys.argv[1:])

    try:
        hook_input = read_input_as(SessionStartInput)
    except HookInputError as exc:
        exit(
            1,
            text=f"[session_start] Hook input error: {exc}",
            to_stderr=True,
            hook_event_name=HOOK_EVENT_NAME,
        )

    if not config.rules:
        exit(hook_event_name=HOOK_EVENT_NAME)

    include_files, include_text = _resolve_includes(config, hook_input.source)
    if not include_files and not include_text:
        exit(hook_event_name=HOOK_EVENT_NAME)

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
        print(f"[session_start] Unresolved placeholders: {', '.join(warning_parts)}", file=sys.stderr)
    if content:
        exit(
            output=HookOutput(
                hook_specific_output=SessionStartOutput(additional_context=content)
            ),
            hook_event_name=HOOK_EVENT_NAME,
        )

    exit(hook_event_name=HOOK_EVENT_NAME)


if __name__ == "__main__":
    raise SystemExit(main())
