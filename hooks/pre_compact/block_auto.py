#!/usr/bin/env python3
"""PreCompact hook to block automatic compaction.

This hook prevents auto-compaction (triggered when context window is full)
while allowing manual compaction via the /compact command.

Use case: When you want full control over when compaction happens, preventing
the system from automatically compressing your conversation context.
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

# add hooks dir to path for rel import
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils import (  # type: ignore
    HookInputError,
    PreCompactInput,
    exit,
    get_toml_section,
    load_toml,
    read_input_as,
)


def _parse_args(argv: list[str]) -> None:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--config-file", default="", help="Path to TOML config file")
    args = parser.parse_args(argv)

    try:
        config_data = load_toml(args.config_file)
    except OSError as exc:
        exit(1, text=f"[block_auto_compact] Config file error: {exc}", to_stderr=True)
    except Exception as exc:
        exit(1, text=f"[block_auto_compact] Config parse error: {exc}", to_stderr=True)

    get_toml_section(config_data, "hooks", "pre_compact", "block_auto")


def main():
    """Entry point for the hook script."""
    _parse_args(sys.argv[1:])
    try:
        hook_input = read_input_as(PreCompactInput)
    except HookInputError as exc:
        exit(1, text=f"[block_auto_compact] Hook input error: {exc}", to_stderr=True)

    if hook_input.trigger == "auto":
        # Block auto-compaction
        exit(
            output={
                "continue": False,
                "stopReason": "Auto compaction blocked by hook. Use /compact manually when ready.",
            }
        )

    # Allow manual compaction to proceed
    exit()


if __name__ == "__main__":
    raise SystemExit(main())
