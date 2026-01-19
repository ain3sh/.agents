#!/usr/bin/env python3
"""PostToolUse hook to remind agent of core operating principles after specific tool uses.

This hook injects reminders from commands/reminders.md into the agent's context
after it updates its todo list (TodoWrite tool). This helps reinforce good
practices at key moments during task execution.

Trigger: PostToolUse (after TodoWrite)
Output: Emits reminders as additional context
"""
from __future__ import annotations
import sys
from pathlib import Path

# add hooks dir to path for rel import
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils import (  # type: ignore
    HookInputError,
    PostToolUseInput,
    emit,
    env_path,
    exit,
    get_project_dir,
    read_input_as,
)


# ============================================================================
# Configuration
# ============================================================================

# NOTE: Tool filtering is handled by the "matcher" field in settings.json,
# not here. Configure which tools trigger this hook via:
#   "PostToolUse": [{ "matcher": "TodoWrite", "hooks": [...] }]


def get_reminders_path() -> Path:
    """Get path to the reminders command file.

    Checks workspace commands first, then falls back to user commands.
    """
    # Try workspace-level commands first (takes precedence)
    project_dir = get_project_dir()
    if project_dir:
        workspace_path = project_dir / ".factory" / "commands" / "reminders.md"
        if workspace_path.exists():
            return workspace_path

    # Fall back to user-level commands
    user_path = env_path("FACTORY_USER_DIR", Path.home() / ".factory") or (Path.home() / ".factory")
    return user_path / "commands" / "reminders.md"


def load_reminders() -> str | None:
    """Load reminders from the command file.

    Returns None if the file doesn't exist or can't be read.
    """
    path = get_reminders_path()
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


# ============================================================================
# Main Hook Logic
# ============================================================================

def handle_post_tool_use(hook_input: PostToolUseInput) -> None:
    """Handle PostToolUse hook - inject reminders after matched tool uses.

    Args:
        hook_input: Parsed PostToolUse hook input containing tool_name,
                   tool_input, and tool_response

    Note: Tool filtering is done by the matcher in settings.json, so this
    function only runs for tools that match the configured pattern.
    """
    reminders = load_reminders()
    if reminders:
        emit(text=f"[Agent Reminders]\n{reminders}")


def main():
    """Entry point for the hook script."""
    try:
        hook_input = read_input_as(PostToolUseInput)
    except HookInputError as exc:
        exit(1, text=f"[agent_reminders] Hook input error: {exc}", to_stderr=True)

    handle_post_tool_use(hook_input)
    exit()


if __name__ == "__main__":
    raise SystemExit(main())
