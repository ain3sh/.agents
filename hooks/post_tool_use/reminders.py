#!/usr/bin/env python3
"""PostToolUse hook to remind agent of core operating principles after specific tool uses.

This hook injects reminders from commands/reminders.md into the agent's context
after it updates its todo list (TodoWrite tool). This helps reinforce good
practices at key moments during task execution.

Trigger: PostToolUse (after TodoWrite)
Output: Emits reminders as additional context
"""
from __future__ import annotations
import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

# add hooks dir to path for rel import
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils import (  # type: ignore
    HookInputError,
    PostToolUseInput,
    env_path,
    exit,
    get_toml_section,
    get_project_dir,
    load_toml,
    read_input_as,
)


# ============================================================================
# Configuration
# ============================================================================

@dataclass(slots=True, frozen=True)
class Config:
    reminders_path: Path | None


# NOTE: Tool filtering is handled by the "matcher" field in settings.json,
# not here. Configure which tools trigger this hook via:
#   "PostToolUse": [{ "matcher": "TodoWrite", "hooks": [...] }]


def _parse_args(argv: list[str]) -> Config:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--config-file", default="", help="Path to TOML config file")
    args = parser.parse_args(argv)

    try:
        config_data = load_toml(args.config_file)
    except OSError as exc:
        exit(1, text=f"[agent_reminders] Config file error: {exc}", to_stderr=True)
    except Exception as exc:
        exit(1, text=f"[agent_reminders] Config parse error: {exc}", to_stderr=True)

    config = get_toml_section(config_data, "hooks", "post_tool_use", "reminders")
    reminders_path = config.get("path") or config.get("reminders_path")
    path = Path(reminders_path).expanduser() if isinstance(reminders_path, str) else None
    return Config(reminders_path=path)


def get_reminders_path(config: Config) -> Path:
    """Get path to the reminders command file.

    Checks workspace commands first, then falls back to user commands.
    """
    if config.reminders_path is not None:
        return config.reminders_path

    # Try workspace-level commands first (takes precedence)
    project_dir = get_project_dir()
    if project_dir:
        workspace_path = project_dir / ".factory" / "commands" / "reminders.md"
        if workspace_path.exists():
            return workspace_path

    # Fall back to user-level commands
    user_path = env_path("FACTORY_USER_DIR", Path.home() / ".factory") or (Path.home() / ".factory")
    return user_path / "commands" / "reminders.md"


def load_reminders(config: Config) -> str | None:
    """Load reminders from the command file.

    Returns None if the file doesn't exist or can't be read.
    """
    path = get_reminders_path(config)
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

def handle_post_tool_use(hook_input: PostToolUseInput, config: Config) -> str | None:
    """Handle PostToolUse hook - inject reminders after matched tool uses.

    Args:
        hook_input: Parsed PostToolUse hook input containing tool_name,
                   tool_input, and tool_response

    Note: Tool filtering is done by the matcher in settings.json, so this
    function only runs for tools that match the configured pattern.
    """
    reminders = load_reminders(config)
    if reminders:
        return f"[Agent Reminders]\n{reminders}"
    return None


def main():
    """Entry point for the hook script."""
    config = _parse_args(sys.argv[1:])

    try:
        hook_input = read_input_as(PostToolUseInput)
    except HookInputError as exc:
        exit(1, text=f"[agent_reminders] Hook input error: {exc}", to_stderr=True)

    text = handle_post_tool_use(hook_input, config)
    if text:
        exit(text=text)
    exit()


if __name__ == "__main__":
    raise SystemExit(main())
