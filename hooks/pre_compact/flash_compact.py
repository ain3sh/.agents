#!/usr/bin/env python3
"""Generate and persist a Morph flash-compact checkpoint before compaction."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils import (  # type: ignore
    HookInputError,
    PreCompactInput,
    exit,
    get_toml_section,
    load_toml,
    read_input_as,
)
from utils.flash_compact import (  # type: ignore
    CompactViewConfig,
    build_compact_messages,
    determine_query,
    extract_compact_entries,
    load_flash_compact_defaults,
    load_session_budget_state,
    morph_compact_messages,
    record_checkpoint,
    save_session_budget_state,
    state_root,
    tail_messages_within_token_budget,
)

HOOK_EVENT_NAME = "PreCompact"


@dataclass(slots=True, frozen=True)
class Config:
    enabled: bool
    debug: bool
    state_dir: Path
    morph_api_url: str
    env_files: tuple[Path, ...]
    compression_ratio: float
    preserve_recent: int
    compact_prefix_max_tokens: int
    include_markers: bool
    use_typed_reducers: bool
    recent_turns_raw: int
    execute_short_output_chars: int
    execute_head_lines: int
    execute_tail_lines: int
    execute_max_signal_lines: int
    read_large_output_chars: int
    todo_keep_latest_old: bool
    fail_open: bool


def load_config(argv: list[str]) -> Config:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--config-file", default="", help="Path to TOML config file")
    parser.add_argument("--env-file", action="append", default=[], help="Path to a .env file that provides MORPH_API_KEY (repeatable)")
    args = parser.parse_args(argv)

    try:
        config_data = load_toml(args.config_file)
    except OSError as exc:
        exit(1, text=f"[flash_compact] Config file error: {exc}", to_stderr=True, hook_event_name=HOOK_EVENT_NAME)
    except Exception as exc:
        exit(1, text=f"[flash_compact] Config parse error: {exc}", to_stderr=True, hook_event_name=HOOK_EVENT_NAME)

    config = get_toml_section(config_data, "hooks", "pre_compact", "flash_compact")
    defaults = load_flash_compact_defaults(config_data)
    return Config(
        enabled=bool(config.get("enabled", True)),
        debug=bool(config.get("debug", False)),
        state_dir=state_root(config.get("state_dir"), config_data=config_data),
        morph_api_url=str(config.get("morph_api_url") or defaults.morph_api_url),
        env_files=tuple(Path(value).expanduser() for value in args.env_file) or defaults.env_files,
        compression_ratio=float(config.get("compression_ratio", 0.35) or 0.35),
        preserve_recent=int(config.get("preserve_recent", 4) or 0),
        compact_prefix_max_tokens=int(config.get("compact_prefix_max_tokens", 120000) or 0),
        include_markers=bool(config.get("include_markers", False)),
        use_typed_reducers=bool(config.get("use_typed_reducers", True)),
        recent_turns_raw=int(config.get("recent_turns_raw", 4) or 0),
        execute_short_output_chars=int(config.get("execute_short_output_chars", 3000) or 0),
        execute_head_lines=int(config.get("execute_head_lines", 20) or 0),
        execute_tail_lines=int(config.get("execute_tail_lines", 30) or 0),
        execute_max_signal_lines=int(config.get("execute_max_signal_lines", 80) or 0),
        read_large_output_chars=int(config.get("read_large_output_chars", 4000) or 0),
        todo_keep_latest_old=bool(config.get("todo_keep_latest_old", True)),
        fail_open=bool(config.get("fail_open", True)),
    )


def debug_log(config: Config, message: str) -> None:
    if config.debug:
        print(f"[flash_compact] {message}", file=sys.stderr)


def main() -> None:
    config = load_config(sys.argv[1:])
    if not config.enabled:
        exit(hook_event_name=HOOK_EVENT_NAME)

    try:
        hook_input = read_input_as(PreCompactInput)
    except HookInputError as exc:
        exit(1, text=f"[flash_compact] Hook input error: {exc}", to_stderr=True, hook_event_name=HOOK_EVENT_NAME)

    try:
        state = load_session_budget_state(
            root=config.state_dir,
            session_id=hook_input.session_id,
            transcript_path=hook_input.transcript_path,
            cwd=hook_input.cwd,
        )
        transcript_path = Path(hook_input.transcript_path).expanduser()
        entries = extract_compact_entries(transcript_path)
        if not entries:
            debug_log(config, "no messages available for flash-compaction")
            exit(hook_event_name=HOOK_EVENT_NAME)

        latest_user_prompt = ""
        user_turn_count = 0
        for entry in entries:
            user_turn_count = max(user_turn_count, entry.turn_index)
            if entry.role == "user" and entry.kind == "user_text":
                latest_user_prompt = entry.content

        query = determine_query(
            custom_instructions=hook_input.custom_instructions,
            pending_query=state.pending_query,
            latest_user_prompt=latest_user_prompt,
        )
        messages = build_compact_messages(
            entries,
            query=query,
            preserve_recent=config.preserve_recent,
            config=CompactViewConfig(
                use_typed_reducers=config.use_typed_reducers,
                recent_turns_raw=config.recent_turns_raw,
                execute_short_output_chars=config.execute_short_output_chars,
                execute_head_lines=config.execute_head_lines,
                execute_tail_lines=config.execute_tail_lines,
                execute_max_signal_lines=config.execute_max_signal_lines,
                read_large_output_chars=config.read_large_output_chars,
                todo_keep_latest_old=config.todo_keep_latest_old,
            ),
        )
        if not messages:
            debug_log(config, "no compact-view messages available after reducers")
            exit(hook_event_name=HOOK_EVENT_NAME)
        messages = tail_messages_within_token_budget(
            messages,
            config.compact_prefix_max_tokens,
            config.preserve_recent,
        )
        result = morph_compact_messages(
            messages=messages,
            query=query,
            compression_ratio=config.compression_ratio,
            preserve_recent=config.preserve_recent,
            include_markers=config.include_markers,
            api_url=config.morph_api_url,
            env_files=config.env_files,
        )

        compacted_output = str(result.get("output") or "").strip()
        if not compacted_output:
            debug_log(config, "Morph returned empty output")
            exit(hook_event_name=HOOK_EVENT_NAME)

        usage = result.get("usage")
        usage_dict = usage if isinstance(usage, dict) else {}
        metadata = record_checkpoint(
            root=config.state_dir,
            state=state,
            query=query,
            compact_output=compacted_output,
            usage=usage_dict,
        )

        state.last_compact_user_turn_count = user_turn_count
        state.last_advisory_user_turn_count = user_turn_count
        state.last_compact_tokens = metadata.output_tokens or metadata.input_tokens or state.last_compact_tokens
        state.last_estimated_tokens = metadata.input_tokens or state.last_estimated_tokens
        state.pending_query = ""
        save_session_budget_state(config.state_dir, state)
        exit(hook_event_name=HOOK_EVENT_NAME)
    except Exception as exc:
        if config.fail_open:
            debug_log(config, f"fail-open after error: {exc}")
            exit(hook_event_name=HOOK_EVENT_NAME)
        exit(1, text=f"[flash_compact] {exc}", to_stderr=True, hook_event_name=HOOK_EVENT_NAME)


if __name__ == "__main__":
    raise SystemExit(main())
