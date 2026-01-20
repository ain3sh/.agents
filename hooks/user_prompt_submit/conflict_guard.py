#!/usr/bin/env python3
"""UserPromptSubmit hook to detect conflicting instructions in long prompts.

Works identically with Claude Code and Factory Droid CLI.
When a prompt exceeds the token threshold, this hook blocks submission,
saves the prompt to /tmp/prompt-conflicts/, and instructs the user to
submit a short slash command instead that will ask the agent to analyze
the saved prompt for conflicts using the built-in Edit/ApplyPatch tool.
"""
from __future__ import annotations
import argparse
import hashlib, time, os, sys
from typing import Literal
from dataclasses import dataclass
from pathlib import Path

# add hooks dir to path for rel import
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils import (  # type: ignore
    HookInputError,
    UserPromptSubmitInput,
    copy_to_clipboard,
    count_tokens,
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
class Config:
    """Runtime configuration loaded from CLI flags."""

    token_threshold: int
    cache_dir: Path
    skip_prefix: str
    skip_prefix_lower: str  # Cached lowercase version


def load_config(argv: list[str]) -> Config:
    """Load configuration from CLI flags."""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--config-file", default="", help="Path to TOML config file")
    parser.add_argument("--token-threshold", type=int, default=None)
    parser.add_argument("--cache-dir", default="")
    parser.add_argument("--skip-prefix", default=None, help="Optional prefix to skip conflict checking")
    args = parser.parse_args(argv)

    try:
        config_data = load_toml(args.config_file)
    except OSError as exc:
        exit(1, text=f"[prompt_conflict] Config file error: {exc}", to_stderr=True)
    except Exception as exc:
        exit(1, text=f"[prompt_conflict] Config parse error: {exc}", to_stderr=True)

    config = get_toml_section(config_data, "hooks", "user_prompt_submit", "conflict_guard")

    token_threshold = (
        args.token_threshold
        if args.token_threshold is not None
        else config.get("token_threshold", 1800)
    )
    cache_dir = args.cache_dir or config.get("cache_dir") or "/tmp/prompt-conflicts"
    skip_prefix = (
        args.skip_prefix
        if args.skip_prefix is not None
        else config.get("skip_prefix", "")
    )

    skip_prefix = str(skip_prefix or "")

    return Config(
        token_threshold=int(token_threshold),
        cache_dir=Path(str(cache_dir)).expanduser(),
        skip_prefix=skip_prefix,
        skip_prefix_lower=skip_prefix.lower(),
    )


# ============================================================================
# Prompt Storage
# ============================================================================

@dataclass(slots=True, frozen=True)
class StoredPrompt:
    """Information about a prompt saved to disk."""

    path: str


def store_prompt(prompt: str, config: Config, session_id: str) -> StoredPrompt:
    """Save prompt to timestamped file and create/update latest.md symlink."""
    config.cache_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename: timestamp-session-hash.md
    timestamp = int(time.time())
    sess_short = (session_id or "nosession").replace(os.sep, "_")[:8]
    digest = hashlib.sha256(prompt.encode()).hexdigest()[:10]
    filename = f"{timestamp}-{sess_short}-{digest}.md"

    # Write prompt file
    file_path = config.cache_dir / filename
    file_path.write_text(prompt, encoding="utf-8")

    # Create/update latest.md symlink
    latest_path = config.cache_dir / "latest.md"
    try:
        latest_path.unlink(missing_ok=True)
        try:
            latest_path.symlink_to(filename)
        except OSError:
            latest_path.write_text(prompt, encoding="utf-8")
    except OSError:
        pass

    return StoredPrompt(path=str(file_path))


# ============================================================================
# Main Hook Logic
# ============================================================================

Action = Literal["allow", "block"]


def handle_prompt(
    hook_input: UserPromptSubmitInput,
    config: Config,
) -> Action:
    """Decide whether to block a prompt and emit appropriate output.

    Returns "allow" or "block".
    """
    prompt = hook_input.prompt
    stripped = prompt.lstrip()

    # Optional override: skip conflict checking with special prefix
    if config.skip_prefix_lower and stripped.lower().startswith(config.skip_prefix_lower):
        return "allow"

    token_count = count_tokens(prompt)

    # Short prompts always pass through
    if token_count <= config.token_threshold:
        return "allow"

    # Long prompt detected - save to file
    stored = store_prompt(prompt, config, hook_input.session_id)

    # Prepare clipboard shortcut
    slash_command = "/check-conflicts"
    clipboard_hint = (
        f"\n✓ Copied to clipboard: {slash_command}\n   Just paste (Ctrl+V / Cmd+V) and press Enter!"
        if copy_to_clipboard(slash_command)
        else f"\n   Copy and submit: {slash_command}"
    )

    # Block with helpful message
    reason = f"""Prompt too long ({token_count:,} tokens > {config.token_threshold:,} threshold).
Saved to: {stored.path}
{clipboard_hint}

────────────────────────────────────────────────
{slash_command}
────────────────────────────────────────────────

This will ask the agent to analyze the saved prompt for conflicting
or ambiguous instructions using Edit/ApplyPatch with git-diff highlighting.
"""

    emit(output={"decision": "block", "reason": reason})
    return "block"


def main() -> int:
    """Entry point for the hook script."""
    config = load_config(sys.argv[1:])

    try:
        hook_input = read_input_as(UserPromptSubmitInput)
    except HookInputError as exc:
        exit(1, text=f"[prompt_conflict] Hook input error: {exc}", to_stderr=True)

    action = handle_prompt(hook_input, config)

    if action == "allow":
        exit()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())