#!/usr/bin/env python3
"""Budget scheduler for flash-compact."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils import (  # type: ignore
    HookInputError,
    UserPromptSubmitInput,
    copy_to_clipboard,
    count_tokens,
    exit,
    get_toml_section,
    load_toml,
    read_input_as,
)
from utils.flash_compact import (  # type: ignore
    load_flash_compact_defaults,
    load_session_budget_state,
    save_session_budget_state,
    snapshot_transcript,
    state_root,
    store_prompt_cache,
)

HOOK_EVENT_NAME = "UserPromptSubmit"
NON_BLOCKING_PREFIXES = ("/compact", "/compress", "/clear", "/new", "/resume")


@dataclass(slots=True, frozen=True)
class Config:
    enabled: bool
    debug: bool
    state_dir: Path
    prompt_cache_dir: Path
    soft_turn_interval: int
    soft_token_delta: int
    hard_token_threshold: int
    hard_token_delta: int
    cooldown_turns: int
    soft_action: str
    hard_action: str
    max_advisory_chars: int
    fail_open: bool


def load_config(argv: list[str]) -> Config:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--config-file", default="", help="Path to TOML config file")
    args = parser.parse_args(argv)

    try:
        config_data = load_toml(args.config_file)
    except OSError as exc:
        exit(1, text=f"[flash_compact_budget] Config file error: {exc}", to_stderr=True, hook_event_name=HOOK_EVENT_NAME)
    except Exception as exc:
        exit(1, text=f"[flash_compact_budget] Config parse error: {exc}", to_stderr=True, hook_event_name=HOOK_EVENT_NAME)

    config = get_toml_section(config_data, "hooks", "user_prompt_submit", "flash_compact_budget")
    defaults = load_flash_compact_defaults(config_data)
    return Config(
        enabled=bool(config.get("enabled", True)),
        debug=bool(config.get("debug", False)),
        state_dir=state_root(config.get("state_dir"), config_data=config_data),
        prompt_cache_dir=Path(
            str(
                config.get("prompt_cache_dir")
                or defaults.prompt_cache_dir
            )
        ).expanduser(),
        soft_turn_interval=int(config.get("soft_turn_interval", 12) or 0),
        soft_token_delta=int(config.get("soft_token_delta", 30000) or 0),
        hard_token_threshold=int(config.get("hard_token_threshold", 120000) or 0),
        hard_token_delta=int(config.get("hard_token_delta", 60000) or 0),
        cooldown_turns=int(config.get("cooldown_turns", 3) or 0),
        soft_action=str(config.get("soft_action") or "advisory"),
        hard_action=str(config.get("hard_action") or "block"),
        max_advisory_chars=int(config.get("max_advisory_chars", 1200) or 0),
        fail_open=bool(config.get("fail_open", True)),
    )


def is_non_blocking_prompt(prompt: str) -> bool:
    stripped = prompt.lstrip()
    return any(stripped.startswith(prefix) for prefix in NON_BLOCKING_PREFIXES)


def debug_log(config: Config, message: str) -> None:
    if config.debug:
        print(f"[flash_compact_budget] {message}", file=sys.stderr)


def soft_due(config: Config, *, current_user_turn_count: int, estimated_tokens: int, state_last_compact_turn: int, state_last_compact_tokens: int, state_last_advisory_turn: int) -> bool:
    turn_anchor = max(state_last_compact_turn, state_last_advisory_turn)
    turn_due = config.soft_turn_interval > 0 and current_user_turn_count - turn_anchor >= config.soft_turn_interval
    token_due = config.soft_token_delta > 0 and estimated_tokens - state_last_compact_tokens >= config.soft_token_delta
    return turn_due or token_due


def hard_due(config: Config, *, estimated_tokens: int, state_last_compact_tokens: int) -> bool:
    threshold_due = config.hard_token_threshold > 0 and estimated_tokens >= config.hard_token_threshold
    delta_due = config.hard_token_delta > 0 and estimated_tokens - state_last_compact_tokens >= config.hard_token_delta
    return threshold_due or delta_due


def advisory_message(config: Config, *, estimated_tokens: int, soft_trigger: str) -> str:
    message = (
        f"[flash-compact] Context budget nearing limit ({estimated_tokens:,} estimated tokens; {soft_trigger}). "
        "Consider running `/compress` soon."
    )
    if config.max_advisory_chars > 0 and len(message) > config.max_advisory_chars:
        return message[: config.max_advisory_chars].rstrip()
    return message


def hard_block_reason(prompt_path: Path, estimated_tokens: int) -> str:
    slash_command = "/compress"
    clipboard_hint = (
        f"\n✓ Copied to clipboard: {slash_command}\n   Paste it now and press Enter."
        if copy_to_clipboard(slash_command)
        else f"\n   Next step: run `{slash_command}`"
    )
    return (
        f"Context budget exceeded ({estimated_tokens:,} estimated tokens).\n"
        f"Saved your prompt to: {prompt_path}\n"
        f"{clipboard_hint}\n\n"
        "Compact the session first, then resend or reuse the saved prompt."
    )


def main() -> None:
    config = load_config(sys.argv[1:])
    if not config.enabled:
        exit(hook_event_name=HOOK_EVENT_NAME)

    try:
        hook_input = read_input_as(UserPromptSubmitInput)
    except HookInputError as exc:
        exit(1, text=f"[flash_compact_budget] Hook input error: {exc}", to_stderr=True, hook_event_name=HOOK_EVENT_NAME)

    try:
        state = load_session_budget_state(
            root=config.state_dir,
            session_id=hook_input.session_id,
            transcript_path=hook_input.transcript_path,
            cwd=hook_input.cwd,
        )
        snapshot = snapshot_transcript(Path(hook_input.transcript_path).expanduser())

        state.transcript_path = hook_input.transcript_path
        state.cwd = hook_input.cwd

        if is_non_blocking_prompt(hook_input.prompt):
            save_session_budget_state(config.state_dir, state)
            exit(hook_event_name=HOOK_EVENT_NAME)

        state.pending_query = hook_input.prompt.strip()
        current_user_turn_count = snapshot.user_turn_count + 1
        estimated_tokens = snapshot.token_count + count_tokens(hook_input.prompt)
        state.last_seen_user_turn_count = current_user_turn_count
        state.last_estimated_tokens = estimated_tokens

        if current_user_turn_count < state.cooldown_until_user_turn_count:
            debug_log(config, "cooldown active; skipping")
            save_session_budget_state(config.state_dir, state)
            exit(hook_event_name=HOOK_EVENT_NAME)

        is_hard_due = hard_due(
            config,
            estimated_tokens=estimated_tokens,
            state_last_compact_tokens=state.last_compact_tokens,
        )
        if is_hard_due and config.hard_action == "block":
            prompt_path = store_prompt_cache(config.prompt_cache_dir, hook_input.prompt, hook_input.session_id)
            state.blocked_prompt_path = str(prompt_path)
            save_session_budget_state(config.state_dir, state)
            exit(
                output={"decision": "block", "reason": hard_block_reason(prompt_path, estimated_tokens)},
                hook_event_name=HOOK_EVENT_NAME,
            )

        is_soft_due = soft_due(
            config,
            current_user_turn_count=current_user_turn_count,
            estimated_tokens=estimated_tokens,
            state_last_compact_turn=state.last_compact_user_turn_count,
            state_last_compact_tokens=state.last_compact_tokens,
            state_last_advisory_turn=state.last_advisory_user_turn_count,
        )
        if (is_hard_due and config.hard_action == "advisory") or (is_soft_due and config.soft_action == "advisory"):
            trigger = "hard threshold" if is_hard_due and config.hard_action == "advisory" else "soft threshold"
            state.last_advisory_user_turn_count = current_user_turn_count
            state.cooldown_until_user_turn_count = current_user_turn_count + max(config.cooldown_turns, 0)
            save_session_budget_state(config.state_dir, state)
            exit(
                output={"systemMessage": advisory_message(config, estimated_tokens=estimated_tokens, soft_trigger=trigger)},
                hook_event_name=HOOK_EVENT_NAME,
            )

        save_session_budget_state(config.state_dir, state)
        exit(hook_event_name=HOOK_EVENT_NAME)
    except Exception as exc:
        if config.fail_open:
            debug_log(config, f"fail-open after error: {exc}")
            exit(hook_event_name=HOOK_EVENT_NAME)
        exit(1, text=f"[flash_compact_budget] {exc}", to_stderr=True, hook_event_name=HOOK_EVENT_NAME)


if __name__ == "__main__":
    raise SystemExit(main())
