#!/usr/bin/env python3
"""SessionStart hook to load environment variables from vars.env.

This provides a similar UX to Claude Code's "env": {} field in settings.json.
Users can define environment variables in ~/.factory/vars.env (or a custom path)
and they will be automatically loaded into the Droid session on startup.

Compatible with both Factory Droid and Claude Code (when used with appropriate
settings configuration).

Example vars.env:
    # Hook configuration
    LONG_PROMPT_THRESHOLD=2000
    PROMPT_CONFLICT_ALWAYS_ON=false

    # API keys (be careful with sensitive data!)
    # MY_API_KEY=secret

Usage in ~/.factory/settings.json:
    {
      "hooks": {
        "SessionStart": [
          {
            "matcher": "startup",
            "hooks": [
              {
                "type": "command",
                "command": "/home/user/.factory/hooks/session_start/env_vars.py",
                "timeout": 5
              }
            ]
          }
        ]
      }
    }
"""
from __future__ import annotations
import argparse
import os, re, sys
from pathlib import Path

# add hooks dir to path for rel import
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils import (  # type: ignore
    HookInputError,
    SessionStartInput,
    env_path,
    exit,
    get_droid_env_file,
    read_input_as,
    set_env,
)


# ============================================================================
# Configuration
# ============================================================================

# Default location for vars.env
DEFAULT_VARS_FILE = Path.home() / ".factory" / "vars.env"

# Regex for parsing env file lines: KEY=value or KEY="value" or KEY='value'
# Supports:
#   - Simple: KEY=value
#   - Quoted: KEY="value with spaces" or KEY='value'
#   - Export prefix: export KEY=value
ENV_LINE_PATTERN = re.compile(
    r'^(?:export\s+)?'           # Optional 'export ' prefix
    r'([A-Za-z_][A-Za-z0-9_]*)'  # Variable name
    r'='                          # Equals sign
    r'(.*)$'                      # Value (everything after =)
)


# ============================================================================
# Env File Parsing
# ============================================================================

def parse_env_text(text: str) -> dict[str, str]:
    """Parse .env formatted text and return a dict of variables.

    Supports:
    - Comments (lines starting with #)
    - Empty lines
    - KEY=value format
    - KEY="quoted value" format
    - KEY='single quoted value' format
    - export KEY=value format
    - Inline comments: KEY=value # comment

    Args:
        text: Raw .env text

    Returns:
        Dict of environment variable names to values
    """
    env_vars: dict[str, str] = {}

    for line in text.splitlines():
        line = line.strip()

        # Skip empty lines and comments
        if not line or line.startswith("#"):
            continue

        match = ENV_LINE_PATTERN.match(line)
        if not match:
            # Invalid line - skip silently (could log in debug mode)
            continue

        key = match.group(1)
        value = match.group(2).strip()

        # Handle quoted values
        if (value.startswith('"') and value.endswith('"')) or \
           (value.startswith("'") and value.endswith("'")):
            value = value[1:-1]
        else:
            # Remove inline comments for unquoted values
            if " #" in value:
                value = value.split(" #", 1)[0].strip()

        env_vars[key] = value

    return env_vars


def parse_env_file(file_path: Path, *, strict: bool = False) -> dict[str, str]:
    """Parse a .env file and return a dict of variables."""
    if not file_path.exists():
        if strict:
            raise FileNotFoundError(str(file_path))
        return {}

    try:
        text = file_path.read_text(encoding="utf-8")
    except OSError:
        if strict:
            raise
        return {}

    return parse_env_text(text)


def parse_env_files(file_paths: list[Path], *, strict: bool = False) -> dict[str, str]:
    """Parse one or more .env files and merge them (last writer wins)."""
    merged: dict[str, str] = {}
    for file_path in file_paths:
        merged.update(parse_env_file(file_path, strict=strict))
    return merged


def apply_env_vars(env_vars: dict[str, str]) -> int:
    """Persist a set of environment variables into the agent session env file."""
    env_file = get_droid_env_file()
    if env_file is None:
        # No session env-file available (neither DROID_ENV_FILE nor CLAUDE_ENV_FILE).
        # Fall back to setting in current process.
        for key, value in env_vars.items():
            os.environ[key] = value
        return len(env_vars)

    # Write all vars to DROID_ENV_FILE
    count = 0
    for key, value in env_vars.items():
        if set_env(key, value):
            count += 1

    return count


def load_env_vars(vars_file: Path, *, strict: bool = False) -> int:
    """Load environment variables from file into the agent session env file."""
    env_vars = parse_env_file(vars_file, strict=strict)
    return apply_env_vars(env_vars)


# ============================================================================
# CLI
# ============================================================================

def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--vars-file", action="append", default=[], help="Path to .env file (repeatable)")
    parser.add_argument("--strict", action="store_true", help="Fail if a specified file is missing/unreadable")
    parser.add_argument("--verbose", action="store_true", help="Print which source was used")
    return parser.parse_args(argv)


# ============================================================================
# Main Hook Logic
# ============================================================================

def main():
    """Entry point for the hook script."""
    args = _parse_args(sys.argv[1:])

    # Determine vars file location
    vars_files: list[Path]
    if args.vars_file:
        vars_files = [Path(p).expanduser() for p in args.vars_file]
    else:
        vars_file = env_path("DROID_VARS_FILE", DEFAULT_VARS_FILE) or DEFAULT_VARS_FILE
        vars_files = [vars_file]

    # Parse hook input to verify we're in a SessionStart context
    try:
        hook_input = read_input_as(SessionStartInput)
    except HookInputError as exc:
        exit(1, text=f"[env_vars] Hook input error: {exc}", to_stderr=True)

    # Only load on startup (not resume/clear/compact)
    if hook_input.source != "startup":
        exit()

    env_vars = parse_env_files(vars_files, strict=bool(args.strict))
    if not env_vars:
        exit()

    count = apply_env_vars(env_vars)

    if count > 0:
        # Output is shown to user in transcript mode
        if args.vars_file:
            sources = ", ".join(str(p) for p in vars_files)
            print(f"[env_vars] Loaded {count} environment variable(s) from {sources}")
        elif args.verbose:
            print(f"[env_vars] Loaded {count} environment variable(s) from {vars_files[0]}")

    exit()


if __name__ == "__main__":
    raise SystemExit(main())