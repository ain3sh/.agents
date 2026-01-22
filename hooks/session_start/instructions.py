#!/usr/bin/env python3
"""SessionStart hook to inject default instructions from a base directory."""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

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


@dataclass(slots=True, frozen=True)
class Config:
    prompts_dir: Path
    include_files: tuple[str, ...]
    sources: set[str]


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
        exit(1, text=f"[session_start] Config file error: {exc}", to_stderr=True)
    except Exception as exc:
        exit(1, text=f"[session_start] Config parse error: {exc}", to_stderr=True)

    config = get_toml_section(config_data, "hooks", "session_start", "instructions")
    config_prompts = config.get("prompts_dir")
    if args.prompts_dir:
        prompts_dir_value = args.prompts_dir
    elif isinstance(config_prompts, str) and config_prompts:
        prompts_dir_value = config_prompts
    else:
        prompts_dir_value = "~/.agents/prompts"

    include_files = config.get("include")
    if isinstance(include_files, str):
        include = (include_files,) if include_files else ()
    elif isinstance(include_files, list):
        include = tuple(item for item in include_files if isinstance(item, str))
    else:
        include = ()

    if not include:
        include = ("BASICS.md",)

    sources_value = config.get("when") or config.get("sources")
    if isinstance(sources_value, list):
        sources = {item for item in sources_value if isinstance(item, str)}
    else:
        sources = {"startup", "resume", "clear", "compact"}

    return Config(
        prompts_dir=Path(prompts_dir_value).expanduser(),
        include_files=include,
        sources=sources,
    )


def _read_text(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        content = path.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return content or None


def _compose_instructions(prompts_dir: Path, include_files: tuple[str, ...]) -> str | None:
    contents: list[str] = []
    for filename in include_files or ("BASICS.md",):
        text = _read_text(prompts_dir / filename)
        if text:
            contents.append(text)
    if not contents:
        return None
    return "\n\n".join(contents)


def main():
    config = _parse_args(sys.argv[1:])

    try:
        hook_input = read_input_as(SessionStartInput)
    except HookInputError as exc:
        exit(1, text=f"[session_start] Hook input error: {exc}", to_stderr=True)

    if hook_input.source not in config.sources:
        exit()

    content = _compose_instructions(config.prompts_dir, config.include_files)
    if content:
        exit(
            output=HookOutput(
                hook_specific_output=SessionStartOutput(additional_context=content)
            )
        )

    exit()


if __name__ == "__main__":
    raise SystemExit(main())
