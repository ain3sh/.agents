#!/usr/bin/env python3
"""PreToolUse hook: guard Execute/Bash commands via `tirith check`.

Configurable under [hooks.pre_tool_use.tirith] in droid.toml. Fail-open by
default so a missing binary / timeout doesn't block legitimate work.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils import (  # type: ignore
    HookInputError,
    PreToolUseInput,
    exit,
    get_toml_section,
    load_toml,
    read_input_as,
)

HOOK_EVENT_NAME = "PreToolUse"
DEFAULT_TOOLS = ("Execute", "Bash")
DEFAULT_TIMEOUT = 5
TIRITH_EXIT_OK = 0
TIRITH_EXIT_WARN_ACK = 3


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--config-file", default="", help="Path to TOML config file")
    return parser.parse_args(argv)


def _load_config(path: str) -> dict:
    if not path:
        return {}
    try:
        return load_toml(path)
    except OSError as exc:
        exit(1, text=f"[tirith] config error: {exc}", to_stderr=True, hook_event_name=HOOK_EVENT_NAME)
    except Exception as exc:
        exit(1, text=f"[tirith] config parse error: {exc}", to_stderr=True, hook_event_name=HOOK_EVENT_NAME)


def _tools_set(cfg: dict) -> set[str]:
    raw = cfg.get("tools")
    if isinstance(raw, list):
        return {t for t in raw if isinstance(t, str) and t}
    return set(DEFAULT_TOOLS)


def _resolve_tirith() -> str | None:
    # Hook subprocess PATH may not include ~/.local/bin.
    found = shutil.which("tirith")
    if found:
        return found
    for candidate in (
        Path.home() / ".local/bin/tirith",
        Path("/usr/local/bin/tirith"),
        Path("/opt/homebrew/bin/tirith"),
        Path("/usr/bin/tirith"),
    ):
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    return None


def _tirith_check(command: str, timeout: int) -> tuple[int, str]:
    """Return (exit_code, detail). exit_code < 0 signals exec failure."""
    env = {**os.environ, "TIRITH_INTEGRATION": os.environ.get("TIRITH_INTEGRATION", "droid-cli")}
    binary = _resolve_tirith()
    if not binary:
        return -1, "tirith binary not found"
    try:
        result = subprocess.run(
            [binary, "check", "--format", "json", "--non-interactive", "--", command],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            env=env,
        )
    except subprocess.TimeoutExpired:
        return -1, f"tirith check timed out after {timeout}s"
    except (FileNotFoundError, OSError) as exc:
        return -1, f"tirith exec error: {exc}"

    detail = (result.stdout or "").strip() or (result.stderr or "").strip()
    return result.returncode, detail


def _extract_reason(detail: str) -> str:
    if not detail:
        return "tirith blocked this command"
    try:
        data = json.loads(detail)
    except (ValueError, TypeError):
        return detail[:400]

    findings = data.get("findings") if isinstance(data, dict) else None
    if isinstance(findings, list) and findings:
        parts = []
        for f in findings[:3]:
            if not isinstance(f, dict):
                continue
            rule = f.get("rule_id") or f.get("rule") or "?"
            sev = f.get("severity", "?")
            msg = f.get("title") or f.get("message") or f.get("description") or f.get("reason") or ""
            msg = " ".join(msg.split()) if isinstance(msg, str) else ""
            parts.append(f"[{sev}] {rule}: {msg}")
        if parts:
            return " | ".join(parts)[:400]

    if isinstance(data, dict):
        msg = data.get("message") or data.get("reason")
        if isinstance(msg, str) and msg:
            return msg[:400]

    return "tirith blocked this command"


def main() -> int | None:
    args = _parse_args(sys.argv[1:])
    config_data = _load_config(args.config_file)
    config = get_toml_section(config_data, "hooks", "pre_tool_use", "tirith")

    if not bool(config.get("enabled", True)):
        exit(hook_event_name=HOOK_EVENT_NAME)

    fail_mode = str(config.get("fail_mode", "open")).lower()
    if fail_mode not in ("open", "closed"):
        fail_mode = "open"

    try:
        timeout = int(config.get("timeout", DEFAULT_TIMEOUT))
    except (TypeError, ValueError):
        timeout = DEFAULT_TIMEOUT

    supported_tools = _tools_set(config)

    try:
        hook_input = read_input_as(PreToolUseInput)
    except HookInputError as exc:
        exit(1, text=f"[tirith] hook input error: {exc}", to_stderr=True, hook_event_name=HOOK_EVENT_NAME)

    if hook_input.tool_name not in supported_tools:
        exit(hook_event_name=HOOK_EVENT_NAME)

    command = str(hook_input.tool_input.get("command", "")).strip()
    if not command:
        exit(hook_event_name=HOOK_EVENT_NAME)

    code, detail = _tirith_check(command, timeout)

    if code == TIRITH_EXIT_OK:
        exit(hook_event_name=HOOK_EVENT_NAME)

    if code == TIRITH_EXIT_WARN_ACK:
        # Warn-ack needs an interactive prompt; hooks are non-interactive, so pass through with a transcript note.
        exit(
            text=f"[tirith] warning (not blocking): {_extract_reason(detail)}",
            to_stderr=True,
            hook_event_name=HOOK_EVENT_NAME,
        )

    if code < 0:
        if fail_mode == "closed":
            exit(
                decision="deny",
                reason=f"[tirith] guard unavailable (fail_mode=closed): {detail[:200]}",
                hook_event_name=HOOK_EVENT_NAME,
            )
        exit(
            text=f"[tirith] soft-fail (fail_mode=open): {detail[:200]}",
            to_stderr=True,
            hook_event_name=HOOK_EVENT_NAME,
        )

    exit(
        decision="deny",
        reason=f"[tirith] {_extract_reason(detail)}",
        hook_event_name=HOOK_EVENT_NAME,
    )


if __name__ == "__main__":
    raise SystemExit(main())
