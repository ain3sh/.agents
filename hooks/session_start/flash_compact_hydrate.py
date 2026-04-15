#!/usr/bin/env python3
"""Hydrate a new session from the latest flash-compact checkpoint."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import sys

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
from utils.flash_compact import (  # type: ignore
    load_latest_checkpoint,
    read_checkpoint_output,
    state_root,
    truncate_text,
)

HOOK_EVENT_NAME = "SessionStart"


@dataclass(slots=True, frozen=True)
class Config:
    enabled: bool
    debug: bool
    state_dir: Path
    sources: set[str]
    max_injected_chars: int
    fail_open: bool


def load_config(argv: list[str]) -> Config:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--config-file", default="", help="Path to TOML config file")
    args = parser.parse_args(argv)

    try:
        config_data = load_toml(args.config_file)
    except OSError as exc:
        exit(1, text=f"[flash_compact_hydrate] Config file error: {exc}", to_stderr=True, hook_event_name=HOOK_EVENT_NAME)
    except Exception as exc:
        exit(1, text=f"[flash_compact_hydrate] Config parse error: {exc}", to_stderr=True, hook_event_name=HOOK_EVENT_NAME)

    config = get_toml_section(config_data, "hooks", "session_start", "flash_compact_hydrate")
    raw_sources = config.get("sources", ["compact", "resume"])
    sources = {str(item) for item in raw_sources} if isinstance(raw_sources, list) else {"compact", "resume"}
    return Config(
        enabled=bool(config.get("enabled", True)),
        debug=bool(config.get("debug", False)),
        state_dir=state_root(config.get("state_dir"), config_data=config_data),
        sources=sources,
        max_injected_chars=int(config.get("max_injected_chars", 6000) or 0),
        fail_open=bool(config.get("fail_open", True)),
    )


def debug_log(config: Config, message: str) -> None:
    if config.debug:
        print(f"[flash_compact_hydrate] {message}", file=sys.stderr)


def render_context(output: str, *, query: str, created_at: str, blocked_prompt_path: str) -> str:
    lines = [
        "[flash-compact] This session is continuing from a recent Morph-compacted checkpoint.",
        f"[flash-compact] Created: {created_at}",
        f"[flash-compact] Query: {query}",
        "",
        "Treat the checkpoint below as the best available compressed history unless newer context contradicts it.",
        "",
        output,
    ]
    if blocked_prompt_path:
        lines.extend(
            [
                "",
                f"[flash-compact] If compaction was triggered to recover a blocked prompt, it is saved at: {blocked_prompt_path}",
            ]
        )
    return "\n".join(lines).strip()


def main() -> None:
    config = load_config(sys.argv[1:])
    if not config.enabled:
        exit(hook_event_name=HOOK_EVENT_NAME)

    try:
        hook_input = read_input_as(SessionStartInput)
    except HookInputError as exc:
        exit(1, text=f"[flash_compact_hydrate] Hook input error: {exc}", to_stderr=True, hook_event_name=HOOK_EVENT_NAME)

    if hook_input.source not in config.sources:
        exit(hook_event_name=HOOK_EVENT_NAME)

    try:
        metadata = load_latest_checkpoint(config.state_dir, hook_input.cwd)
        if metadata is None:
            debug_log(config, "no checkpoint found for project")
            exit(hook_event_name=HOOK_EVENT_NAME)

        output = read_checkpoint_output(metadata)
        if not output:
            debug_log(config, "checkpoint output missing")
            exit(hook_event_name=HOOK_EVENT_NAME)

        context = render_context(
            truncate_text(output, config.max_injected_chars),
            query=metadata.query,
            created_at=metadata.created_at,
            blocked_prompt_path=metadata.blocked_prompt_path,
        )
        exit(
            output=HookOutput(
                hook_specific_output=SessionStartOutput(additional_context=context)
            ),
            hook_event_name=HOOK_EVENT_NAME,
        )
    except Exception as exc:
        if config.fail_open:
            debug_log(config, f"fail-open after error: {exc}")
            exit(hook_event_name=HOOK_EVENT_NAME)
        exit(1, text=f"[flash_compact_hydrate] {exc}", to_stderr=True, hook_event_name=HOOK_EVENT_NAME)


if __name__ == "__main__":
    raise SystemExit(main())
