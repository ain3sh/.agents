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
import os
import sys
from pathlib import Path

# add hooks dir to path for rel import
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils import (  # type: ignore
    HookInputError,
    SessionStartInput,
    exit,
    get_droid_env_file,
    get_toml_section,
    load_toml,
    parse_env_files,
    read_input_as,
    set_env,
)

HOOK_EVENT_NAME = "SessionStart"


# ============================================================================
# Configuration
# ============================================================================

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


# ============================================================================
# CLI
# ============================================================================

def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--config-file", default="", help="Path to TOML config file")
    parser.add_argument("--vars-file", action="append", default=[], help="Path to secrets .env file (repeatable)")
    parser.add_argument("--strict", action="store_true", help="Fail if a specified file is missing/unreadable")
    parser.add_argument("--verbose", action="store_true", help="Print which source was used")
    return parser.parse_args(argv)


def _resolve_sources(config: dict[str, object]) -> set[str]:
    sources = config.get("when") or config.get("sources")
    if isinstance(sources, list):
        return {value for value in sources if isinstance(value, str)}
    return {"startup", "resume", "clear"}


def _resolve_secrets_files(config: dict[str, object], args: argparse.Namespace) -> list[Path]:
    if args.vars_file:
        return [Path(p).expanduser() for p in args.vars_file]

    secrets = config.get("secrets")
    if isinstance(secrets, str) and secrets:
        return [Path(secrets).expanduser()]

    return []


def _config_env_vars(config: dict[str, object]) -> dict[str, str]:
    env_vars: dict[str, str] = {}
    reserved = {"when", "sources", "secrets", "strict", "verbose"}
    for key, value in config.items():
        if key in reserved:
            continue
        if isinstance(value, (str, int, float, bool)):
            env_vars[key] = str(value)
    return env_vars


# ============================================================================
# Main Hook Logic
# ============================================================================

def main():
    """Entry point for the hook script."""
    args = _parse_args(sys.argv[1:])

    try:
        config_data = load_toml(args.config_file)
    except OSError as exc:
        exit(
            1,
            text=f"[env_vars] Config file error: {exc}",
            to_stderr=True,
            hook_event_name=HOOK_EVENT_NAME,
        )
    except Exception as exc:
        exit(
            1,
            text=f"[env_vars] Config parse error: {exc}",
            to_stderr=True,
            hook_event_name=HOOK_EVENT_NAME,
        )

    config = get_toml_section(config_data, "hooks", "session_start", "environment")

    sources = _resolve_sources(config)
    secrets_files = _resolve_secrets_files(config, args)
    strict = bool(args.strict or config.get("strict", False))
    verbose = bool(args.verbose or config.get("verbose", False))

    # Parse hook input to verify we're in a SessionStart context
    try:
        hook_input = read_input_as(SessionStartInput)
    except HookInputError as exc:
        exit(
            1,
            text=f"[env_vars] Hook input error: {exc}",
            to_stderr=True,
            hook_event_name=HOOK_EVENT_NAME,
        )

    if hook_input.source not in sources:
        exit(hook_event_name=HOOK_EVENT_NAME)

    env_vars: dict[str, str] = {}
    if secrets_files:
        env_vars.update(parse_env_files(secrets_files, strict=strict))

    env_vars.update(_config_env_vars(config))

    if not env_vars:
        exit(hook_event_name=HOOK_EVENT_NAME)

    count = apply_env_vars(env_vars)

    if count > 0:
        # Output is shown to user in transcript mode
        if secrets_files:
            sources = ", ".join(str(p) for p in secrets_files)
            if args.vars_file or verbose:
                print(f"[env_vars] Loaded {count} environment variable(s) from {sources}")
        elif verbose:
            print(f"[env_vars] Loaded {count} environment variable(s) from config")

    exit(hook_event_name=HOOK_EVENT_NAME)


if __name__ == "__main__":
    raise SystemExit(main())