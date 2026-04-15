"""Environment variable utilities for Factory Droid hooks.

Provides helpers to set persistent environment variables via DROID_ENV_FILE
and read common Droid-specific environment variables.
"""

from __future__ import annotations

import os
from pathlib import Path
import re


# ============================================================================
# DROID_ENV_FILE Helpers
# ============================================================================

def get_droid_env_file() -> Path | None:
    """Get the DROID_ENV_FILE path if available.

    This file is used to persist environment variables for the Droid session.
    Write shell export statements to this file to set env vars that persist
    across commands.

    Returns:
        Path to DROID_ENV_FILE if set, None otherwise
    """
    env_file = os.environ.get("DROID_ENV_FILE") or os.environ.get("CLAUDE_ENV_FILE")
    if env_file:
        return Path(env_file)
    return None


# Regex for parsing env file lines: KEY=value or KEY="value" or KEY='value'
ENV_LINE_PATTERN = re.compile(
    r'^(?:export\s+)?'
    r'([A-Za-z_][A-Za-z0-9_]*)'
    r'='
    r'(.*)$'
)


def parse_env_text(text: str) -> dict[str, str]:
    """Parse .env-formatted text into environment variables."""
    env_vars: dict[str, str] = {}

    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        match = ENV_LINE_PATTERN.match(line)
        if not match:
            continue

        key = match.group(1)
        value = match.group(2).strip()
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]
        elif " #" in value:
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


def set_env(key: str, value: str) -> bool:
    """Set a persistent environment variable for the Droid session.

    Writes an export statement to DROID_ENV_FILE.

    Args:
        key: Environment variable name
        value: Environment variable value

    Returns:
        True if successfully written, False if DROID_ENV_FILE not available
    """
    env_file = get_droid_env_file()
    if env_file is None:
        return False

    # Escape single quotes in value for shell safety
    escaped_value = value.replace("'", "'\"'\"'")
    statement = f"export {key}='{escaped_value}'\n"

    with env_file.open("a") as f:
        f.write(statement)
    return True


def set_envs(env_vars: dict[str, str]) -> bool:
    """Set multiple persistent environment variables.

    Args:
        env_vars: Dict of variable names to values

    Returns:
        True if all successfully written, False if DROID_ENV_FILE not available
    """
    env_file = get_droid_env_file()
    if env_file is None:
        return False

    lines: list[str] = []
    for key, value in env_vars.items():
        escaped_value = value.replace("'", "'\"'\"'")
        lines.append(f"export {key}='{escaped_value}'")

    with env_file.open("a") as f:
        f.write("\n".join(lines) + "\n")
    return True


def add_to_path(directory: str | Path, prepend: bool = False) -> bool:
    """Add a directory to PATH for the Droid session.

    Args:
        directory: Directory to add to PATH
        prepend: If True, prepend to PATH; otherwise append

    Returns:
        True if successfully written, False if DROID_ENV_FILE not available
    """
    env_file = get_droid_env_file()
    if env_file is None:
        return False

    dir_str = str(directory)

    # IMPORTANT: The session env-file may be *parsed* rather than shell-sourced.
    # Avoid emitting `${PATH:-...}` which would not be expanded by a parser.
    fallback_path = "/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
    current_path = os.environ.get("PATH") or fallback_path
    new_path = f"{dir_str}:{current_path}" if prepend else f"{current_path}:{dir_str}"

    # Escape single quotes in value for shell safety
    escaped_value = new_path.replace("'", "'\"'\"'")
    statement = f"export PATH='{escaped_value}'\n"

    with env_file.open("a") as f:
        f.write(statement)
    return True


def source_file(file_path: str | Path) -> bool:
    """Source a shell file for the Droid session.

    Useful for activating virtual environments or loading shell configurations.

    Args:
        file_path: Path to file to source

    Returns:
        True if successfully written, False if DROID_ENV_FILE not available
    """
    env_file = get_droid_env_file()
    if env_file is None:
        return False

    statement = f'source "{file_path}"\n'

    with env_file.open("a") as f:
        f.write(statement)
    return True


def activate_venv(venv_path: str | Path) -> bool:
    """Activate a Python virtual environment for the Droid session.

    Args:
        venv_path: Path to the venv directory (e.g., "./venv" or "/path/to/venv")

    Returns:
        True if successfully written, False if DROID_ENV_FILE not available
    """
    venv = Path(venv_path)
    activate_script = venv / "bin" / "activate"
    return source_file(activate_script)


# ============================================================================
# Droid-Specific Environment Variables
# ============================================================================

def get_project_dir() -> Path | None:
    """Get the Factory project directory.

    This is set by Droid to the absolute path where Droid was started.

    Returns:
        Path to project directory if set, None otherwise
    """
    project_dir = os.environ.get("FACTORY_PROJECT_DIR")
    if project_dir:
        return Path(project_dir)
    return None


def get_plugin_root() -> Path | None:
    """Get the Droid plugin root directory.

    This is set when running hooks from a plugin.

    Returns:
        Path to plugin root if set, None otherwise
    """
    plugin_root = os.environ.get("DROID_PLUGIN_ROOT")
    if plugin_root:
        return Path(plugin_root)
    return None


def is_droid_context() -> bool:
    """Check if we're running in a Droid hook context.

    Returns:
        True if running as a Droid hook (FACTORY_PROJECT_DIR is set)
    """
    return os.environ.get("FACTORY_PROJECT_DIR") is not None
