#!/usr/bin/env python3
"""Restore Factory bin wrappers for tools that should defer to system installs."""

from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils import (  # type: ignore
    HookInputError,
    HookOutput,
    SessionStartInput,
    SessionStartOutput,
    exit,
    get_toml_section,
    load_toml,
    read_input_as,
)

HOOK_EVENT_NAME = "SessionStart"
HOME = Path.home()
FACTORY_BIN = HOME / ".factory" / "bin"
DEFAULT_TOOLS = ("rg", "agent-browser", "cua-driver")
DEFAULT_TARGETS = {
    "rg": ("path:/usr/bin/rg", "path:/bin/rg", "path:/usr/local/bin/rg"),
    "agent-browser": ("npm:agent-browser",),
    "cua-driver": ("path:~/.agents/scripts/cua-driver",),
}


@dataclass(slots=True, frozen=True)
class Config:
    when: set[str]
    tools: tuple[str, ...]
    targets: dict[str, tuple[str, ...]]
    verbose: bool


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--config-file", default="", help="Path to TOML config file")
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args(argv)


def _parse_str_list(value: object) -> tuple[str, ...]:
    if isinstance(value, list):
        return tuple(item for item in value if isinstance(item, str) and item)
    if isinstance(value, str) and value:
        return (value,)
    return ()


def _parse_config(args: argparse.Namespace) -> Config:
    try:
        config_data = load_toml(args.config_file)
    except OSError as exc:
        exit(
            1,
            text=f"[tool_wrappers] Config file error: {exc}",
            to_stderr=True,
            hook_event_name=HOOK_EVENT_NAME,
        )
    except Exception as exc:
        exit(
            1,
            text=f"[tool_wrappers] Config parse error: {exc}",
            to_stderr=True,
            hook_event_name=HOOK_EVENT_NAME,
        )

    section = get_toml_section(config_data, "hooks", "session_start", "tool_wrappers")
    when = set(_parse_str_list(section.get("when"))) or {"startup", "resume", "clear"}
    tools = _parse_str_list(section.get("tools")) or DEFAULT_TOOLS

    targets = dict(DEFAULT_TARGETS)
    configured_targets = section.get("targets")
    if isinstance(configured_targets, dict):
        for tool, value in configured_targets.items():
            if not isinstance(tool, str):
                continue
            parsed = _parse_str_list(value)
            if parsed:
                targets[tool] = parsed

    return Config(
        when=when,
        tools=tools,
        targets=targets,
        verbose=bool(args.verbose or section.get("verbose", False)),
    )


def _path_entries_excluding_factory() -> list[Path]:
    entries: list[Path] = []
    factory_bin = FACTORY_BIN.resolve()
    for raw in os.environ.get("PATH", "").split(os.pathsep):
        if not raw:
            continue
        path = Path(raw).expanduser()
        try:
            if path.resolve() == factory_bin:
                continue
        except OSError:
            pass
        entries.append(path)
    return entries


def _executable(path: Path) -> bool:
    return path.is_file() and os.access(path, os.X_OK)


def _candidate_from_path(tool: str) -> Path | None:
    for directory in _path_entries_excluding_factory():
        candidate = directory / tool
        if _executable(candidate):
            return candidate
    return None


def _candidate_from_npm(tool: str) -> Path | None:
    npm = _candidate_from_path("npm")
    if npm is None:
        return None

    try:
        result = subprocess.run(
            [str(npm), "prefix", "-g"],
            check=False,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (OSError, subprocess.SubprocessError):
        return None

    if result.returncode != 0:
        return None

    prefix = Path(result.stdout.strip()).expanduser()
    candidate = prefix / "bin" / tool
    if _executable(candidate):
        return candidate
    return None


def _candidate_from_spec(spec: str, tool: str) -> Path | None:
    if spec.startswith("npm:"):
        return _candidate_from_npm(spec.removeprefix("npm:") or tool)

    path_spec = spec.removeprefix("path:")
    path = Path(path_spec).expanduser()
    if _executable(path):
        return path
    return None


def _resolve_target(tool: str, config: Config) -> Path | None:
    candidates: list[Path | None] = []
    for spec in config.targets.get(tool, ()):
        candidates.append(_candidate_from_spec(spec, tool))
    candidates.append(_candidate_from_path(tool))

    shim = FACTORY_BIN / tool
    try:
        shim_resolved = shim.resolve()
    except OSError:
        shim_resolved = shim

    for candidate in candidates:
        if candidate is None or not _executable(candidate):
            continue
        try:
            if candidate.resolve() == shim_resolved:
                continue
        except OSError:
            pass
        return candidate
    return None


def _wrapper_for(target: Path) -> str:
    quoted_target = shlex.quote(str(target))
    return f'#!/usr/bin/env sh\nexec {quoted_target} "$@"\n'


def _restore_wrapper(tool: str, target: Path) -> bool:
    FACTORY_BIN.mkdir(parents=True, exist_ok=True)
    shim = FACTORY_BIN / tool
    desired = _wrapper_for(target)

    try:
        if shim.read_text() == desired:
            shim.chmod(0o755)
            return False
    except (OSError, UnicodeDecodeError):
        pass

    tmp = shim.with_name(f".{shim.name}.tmp")
    tmp.write_text(desired)
    tmp.chmod(0o755)
    tmp.replace(shim)
    return True


def _exit_session_start(system_message: str | None = None) -> None:
    if system_message:
        exit(
            output=HookOutput(
                suppress_output=True,
                system_message=system_message,
                hook_specific_output=SessionStartOutput(),
            ),
            hook_event_name=HOOK_EVENT_NAME,
        )

    exit(hook_event_name=HOOK_EVENT_NAME)


def main() -> None:
    args = _parse_args(sys.argv[1:])
    config = _parse_config(args)

    try:
        hook_input = read_input_as(SessionStartInput)
    except HookInputError as exc:
        exit(
            1,
            text=f"[tool_wrappers] Hook input error: {exc}",
            to_stderr=True,
            hook_event_name=HOOK_EVENT_NAME,
        )

    if hook_input.source not in config.when and "*" not in config.when:
        _exit_session_start()

    changed: list[str] = []
    missing: list[str] = []

    for tool in config.tools:
        target = _resolve_target(tool, config)
        if target is None:
            missing.append(tool)
            continue
        if _restore_wrapper(tool, target):
            changed.append(f"{tool} -> {target}")

    status: list[str] = []
    if changed and config.verbose:
        status.append("[tool_wrappers] Restored " + ", ".join(changed))
    if missing and config.verbose:
        status.append("[tool_wrappers] Missing target for " + ", ".join(missing))

    _exit_session_start("\n".join(status) if status else None)


if __name__ == "__main__":
    raise SystemExit(main())
