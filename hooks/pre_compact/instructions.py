#!/usr/bin/env python3
"""PreCompact hook to perform actions before compacting session data.

This hook runs before Droid compacts the session. It can be used to:
- Add additional context to manual compaction requests
- Log compaction events
- Perform pre-compaction cleanup

When manual compact is triggered without custom instructions, this hook
loads default instructions from ~/.factory/commands/compact.md.
"""
from __future__ import annotations
import sys
from pathlib import Path

# add hooks dir to path for rel import
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils import (  # type: ignore
    HookInputError,
    PreCompactInput,
    emit,
    env_path,
    exit,
    get_project_dir,
    read_input_as,
)


# ============================================================================
# Configuration
# ============================================================================

def get_default_instructions_path() -> Path:
    """Get path to the default compact instructions file.

    Checks workspace commands first, then falls back to user commands.
    """
    # Try workspace-level commands first (takes precedence)
    project_dir = get_project_dir()
    if project_dir:
        workspace_path = project_dir / ".factory" / "commands" / "compact.md"
        if workspace_path.exists():
            return workspace_path

    # Fall back to user-level commands
    user_path = env_path("FACTORY_USER_DIR", Path.home() / ".factory") or (Path.home() / ".factory")
    return user_path / "commands" / "compact.md"


def load_default_instructions() -> str | None:
    """Load default compact instructions from the command file.

    Returns None if the file doesn't exist or can't be read.
    """
    path = get_default_instructions_path()
    if not path.exists():
        return None

    try:
        content = path.read_text(encoding="utf-8")
        # Strip YAML frontmatter if present (between --- markers)
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                content = parts[2].strip()
        return content.strip() or None
    except OSError:
        return None


def handle_pre_compact(hook_input: PreCompactInput) -> None:
    """Handle PreCompact hook.

    Args:
        hook_input: Parsed PreCompact hook input

    For manual compacts without custom instructions, loads default instructions
    from commands/compact.md and emits them as context for the compaction.
    """
    if hook_input.trigger == "manual":
        if hook_input.custom_instructions:
            # User provided explicit instructions - use those
            emit(
                text=(
                    "[PreCompact] Manual compact with user instructions:\n"
                    f"{hook_input.custom_instructions}"
                )
            )
        else:
            # No custom instructions - try to load defaults from slash command
            default_instructions = load_default_instructions()
            if default_instructions:
                emit(
                    text=(
                        "[PreCompact] Manual compact with default instructions "
                        f"(from commands/compact.md):\n{default_instructions}"
                    )
                )
            else:
                emit(text="[PreCompact] Manual compact requested (no instructions)")
    else:
        # Auto-compact from context window full
        default_instructions = load_default_instructions()
        if default_instructions:
            emit(
                text=(
                    "[PreCompact] Auto-compact triggered (context window full). "
                    f"Using default instructions:\n{default_instructions}"
                )
            )
        else:
            emit(text="[PreCompact] Auto-compact triggered (context window full)")


def main():
    """Entry point for the hook script."""
    try:
        hook_input = read_input_as(PreCompactInput)
    except HookInputError as exc:
        exit(1, text=f"[pre_compact] Hook input error: {exc}", to_stderr=True)

    handle_pre_compact(hook_input)
    exit()


if __name__ == "__main__":
    raise SystemExit(main())