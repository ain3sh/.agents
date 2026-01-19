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
    emit,
    exit,
    read_input_as,
)


@dataclass(slots=True, frozen=True)
class Config:
    base_dir: Path


def _parse_args(argv: list[str]) -> Config:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "--base-dir",
        default=".agents/prompts",
        help="Base directory for instruction files",
    )
    args = parser.parse_args(argv)
    return Config(base_dir=Path(args.base_dir).expanduser())


def _read_text(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        content = path.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return content or None


def _compose_instructions(base_dir: Path) -> str | None:
    base_path = base_dir / "BASE.md"
    base_text = _read_text(base_path)
    if not base_text:
        return None
    return base_text


def main():
    config = _parse_args(sys.argv[1:])

    try:
        read_input_as(SessionStartInput)
    except HookInputError as exc:
        exit(1, text=f"[session_start] Hook input error: {exc}", to_stderr=True)

    content = _compose_instructions(config.base_dir)
    if content:
        emit(
            output=HookOutput(
                hook_specific_output=SessionStartOutput(additional_context=content)
            )
        )

    exit()


if __name__ == "__main__":
    raise SystemExit(main())
