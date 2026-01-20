"""Configuration utilities for Factory Droid hooks.

Provides helpers to parse environment variables with type safety and defaults.
"""

from __future__ import annotations

import os
import tomllib
from pathlib import Path
from typing import Any, TypeVar, overload

T = TypeVar("T")

# Frozenset for faster membership testing of truthy values
_TRUE_VALUES = frozenset({"1", "true", "yes", "on", "y"})
_FALSE_VALUES = frozenset({"0", "false", "no", "off", "n", ""})


def env_str(key: str, default: str = "") -> str:
    """Get string from environment variable.

    Args:
        key: Environment variable name
        default: Default value if not set

    Returns:
        The environment variable value or default
    """
    return os.environ.get(key, default)


def env_bool(key: str, default: bool = False) -> bool:
    """Parse boolean from environment variable.

    Truthy values: 1, true, yes, on, y (case-insensitive)
    Falsy values: 0, false, no, off, n, empty string (case-insensitive)

    Args:
        key: Environment variable name
        default: Default value if not set or unrecognized

    Returns:
        Parsed boolean value
    """
    value = os.environ.get(key)
    if value is None:
        return default

    lower = value.lower().strip()
    if lower in _TRUE_VALUES:
        return True
    if lower in _FALSE_VALUES:
        return False
    return default


def env_int(key: str, default: int = 0) -> int:
    """Parse integer from environment variable.

    Args:
        key: Environment variable name
        default: Default value if not set or invalid

    Returns:
        Parsed integer value
    """
    value = os.environ.get(key)
    if value is None:
        return default

    try:
        return int(value.strip())
    except ValueError:
        return default


def env_float(key: str, default: float = 0.0) -> float:
    """Parse float from environment variable.

    Args:
        key: Environment variable name
        default: Default value if not set or invalid

    Returns:
        Parsed float value
    """
    value = os.environ.get(key)
    if value is None:
        return default

    try:
        return float(value.strip())
    except ValueError:
        return default


def env_path(key: str, default: str | Path | None = None) -> Path | None:
    """Parse Path from environment variable.

    Args:
        key: Environment variable name
        default: Default path if not set

    Returns:
        Path object or default
    """
    value = os.environ.get(key)
    if value:
        return Path(value)
    if default is not None:
        return Path(default) if isinstance(default, str) else default
    return None


def env_list(key: str, sep: str = ",", default: list[str] | None = None) -> list[str]:
    """Parse list from environment variable.

    Args:
        key: Environment variable name
        sep: Separator between items (default: comma)
        default: Default list if not set

    Returns:
        List of strings
    """
    value = os.environ.get(key)
    if value is None:
        return default if default is not None else []

    if not value.strip():
        return []

    return [item.strip() for item in value.split(sep) if item.strip()]


def env_set(key: str, sep: str = ",", default: set[str] | None = None) -> set[str]:
    """Parse set from environment variable.

    Args:
        key: Environment variable name
        sep: Separator between items (default: comma)
        default: Default set if not set

    Returns:
        Set of strings
    """
    return set(env_list(key, sep, list(default) if default else None))


@overload
def env_choice(key: str, choices: list[str], default: str) -> str: ...
@overload
def env_choice(key: str, choices: list[str], default: None = None) -> str | None: ...


def env_choice(key: str, choices: list[str], default: str | None = None) -> str | None:
    """Get environment variable constrained to specific choices.

    Args:
        key: Environment variable name
        choices: Valid values
        default: Default value if not set or invalid

    Returns:
        The value if valid, otherwise default
    """
    value = os.environ.get(key)
    if value is None:
        return default

    if value in choices:
        return value
    return default


def require_env(key: str) -> str:
    """Get required environment variable.

    Args:
        key: Environment variable name

    Returns:
        The environment variable value

    Raises:
        ValueError: If environment variable is not set
    """
    value = os.environ.get(key)
    if value is None:
        raise ValueError(f"Required environment variable '{key}' is not set")
    return value


def read_toml(path: str | Path) -> dict[str, Any]:
    """Read a TOML file and return its contents as a dict.

    Args:
        path: TOML file path

    Returns:
        Parsed TOML data

    Raises:
        FileNotFoundError: If file does not exist
        OSError: If file cannot be read
        tomllib.TOMLDecodeError: If TOML is invalid
    """
    file_path = Path(path).expanduser()
    if not file_path.exists():
        raise FileNotFoundError(str(file_path))
    with file_path.open("rb") as handle:
        return tomllib.load(handle)


def load_toml(path: str | Path | None) -> dict[str, Any]:
    """Load TOML data from a path, returning empty dict if path is None/empty."""
    if not path:
        return {}
    return read_toml(path)


def get_toml_section(data: dict[str, Any], *keys: str) -> dict[str, Any]:
    """Safely retrieve a nested dict section from TOML data.

    Returns empty dict if any key is missing or the path isn't a dict.
    """
    current: Any = data
    for key in keys:
        if not isinstance(current, dict):
            return {}
        current = current.get(key)
    return current if isinstance(current, dict) else {}
