"""I/O utilities for Factory Droid hooks.

Provides unified parsing of stdin JSON input and emission of hook outputs.
"""

from __future__ import annotations

import json
import sys
from typing import Any, NoReturn, TypeVar

from .types import (
    BaseHookInput,
    HookEventName,
    HookInput,
    HookOutput,
    NotificationInput,
    PermissionDecision,
    PostToolUseInput,
    PreCompactInput,
    PreToolUseInput,
    PreToolUseOutput,
    SessionEndInput,
    SessionStartInput,
    StopInput,
    SubagentStopInput,
    UserPromptSubmitInput,
)


class HookInputError(Exception):
    """Raised when hook input cannot be parsed or validated."""


# ============================================================================
# Input Parsing
# ============================================================================

T = TypeVar("T", bound=BaseHookInput)


def _extract_base_fields(data: dict[str, Any]) -> dict[str, Any]:
    """Extract common base fields from hook input data."""
    return {
        "session_id": data.get("session_id", ""),
        "transcript_path": data.get("transcript_path", ""),
        "cwd": data.get("cwd", ""),
        "permission_mode": data.get("permission_mode", "default"),
        "hook_event_name": data.get("hookEventName", ""),
    }

def _extras_from(data: dict[str, Any], defaults: dict[str, Any]) -> dict[str, Any]:
    return {key: data.get(key, default) for key, default in defaults.items()}

def _build_input(
    input_type: type[T],
    data: dict[str, Any],
    defaults: dict[str, Any],
) -> T:
    base = _extract_base_fields(data)
    return input_type(**base, **_extras_from(data, defaults))

_EVENT_DEFAULTS: dict[HookEventName, tuple[type[BaseHookInput], dict[str, Any]]] = {
    "PreToolUse": (PreToolUseInput, {"tool_name": "", "tool_input": {}}),
    "PostToolUse": (
        PostToolUseInput,
        {"tool_name": "", "tool_input": {}, "tool_response": {}},
    ),
    "Notification": (NotificationInput, {"message": ""}),
    "UserPromptSubmit": (UserPromptSubmitInput, {"prompt": ""}),
    "Stop": (StopInput, {"stop_hook_active": False}),
    "SubagentStop": (SubagentStopInput, {"stop_hook_active": False}),
    "PreCompact": (
        PreCompactInput,
        {"trigger": "manual", "custom_instructions": ""},
    ),
    "SessionStart": (SessionStartInput, {"source": "startup"}),
    "SessionEnd": (SessionEndInput, {"reason": "other"}),
}

def read_input() -> HookInput:
    """Read and parse hook input from stdin.

    Automatically detects the hook event type and returns the appropriate
    typed input object.

    Returns:
        Typed hook input based on hook_event_name

    Raises:
        HookInputError: If input cannot be read or parsed
    """
    raw = sys.stdin.read().strip()
    if not raw:
        raise HookInputError("No input received on stdin")

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise HookInputError(f"Invalid JSON: {e}") from e

    if not isinstance(data, dict):
        raise HookInputError("Hook input must be a JSON object")

    event_name = data.get("hookEventName")
    if not event_name:
        raise HookInputError("Missing 'hook_event_name' field")

    event_config = _EVENT_DEFAULTS.get(event_name)
    if event_config is None:
        raise HookInputError(f"Unknown hook event: {event_name}")
    input_type, defaults = event_config
    return _build_input(input_type, data, defaults)

def read_input_as(input_type: type[T]) -> T:
    """Read hook input and validate it matches the expected type.

    Use this when you know which hook event your script handles.

    Example:
        input = read_input_as(UserPromptSubmitInput)
        print(input.prompt)

    Raises:
        HookInputError: If input doesn't match expected type
    """
    hook_input = read_input()
    if not isinstance(hook_input, input_type):
        raise HookInputError(
            f"Expected {input_type.__name__}, got {type(hook_input).__name__}"
        )
    return hook_input


# ============================================================================
# Output + Exit
# ============================================================================

def emit(
    *,
    text: str | None = None,
    output: HookOutput | dict[str, Any] | None = None,
    decision: PermissionDecision | None = None,
    reason: str | None = None,
    updated_input: dict[str, Any] | None = None,
    to_stderr: bool = False,
) -> None:
    if decision is not None:
        output = HookOutput(
            hook_specific_output=PreToolUseOutput(
                permission_decision=decision,
                permission_decision_reason=reason,
                updated_input=updated_input,
            ),
        )
    if output is not None:
        data = output.to_dict() if isinstance(output, HookOutput) else output
        print(json.dumps(data))
    if text is not None:
        print(text, file=sys.stderr if to_stderr else sys.stdout)


def exit(
    code: int = 0,
    *,
    text: str | None = None,
    output: HookOutput | dict[str, Any] | None = None,
    to_stderr: bool = False,
) -> NoReturn:
    if output is not None or text is not None:
        emit(text=text, output=output, to_stderr=to_stderr)
    sys.exit(code)
