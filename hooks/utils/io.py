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
        raise HookInputError("Missing 'hookEventName' field")

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

def _emit(
    *,
    text: str | None = None,
    output: HookOutput | dict[str, Any] | None = None,
    decision: PermissionDecision | None = None,
    reason: str | None = None,
    updated_input: dict[str, Any] | None = None,
    suppress_output: bool = True,
    to_stderr: bool = False,
    hook_event_name: HookEventName | None = None,
) -> None:
    if decision is not None:
        # hookSpecificOutput format with suppressOutput at top level
        hook_output: dict[str, Any] = {
            "hookEventName": "PreToolUse",
            "permissionDecision": decision,
        }
        if reason:
            hook_output["permissionDecisionReason"] = reason
        if updated_input:
            hook_output["updatedInput"] = updated_input

        data: dict[str, Any] = {"hookSpecificOutput": hook_output}
        if suppress_output:
            data["suppressOutput"] = True
        print(json.dumps(data), flush=True)
    elif output is not None:
        if isinstance(output, HookOutput):
            data = output.to_dict()
        else:
            data = dict(output)
            if hook_event_name is not None:
                hook_specific = data.get("hookSpecificOutput")
                if isinstance(hook_specific, dict) and "hookEventName" not in hook_specific:
                    hook_specific["hookEventName"] = hook_event_name
        print(json.dumps(data))
    if text is not None:
        print(text, file=sys.stderr if to_stderr else sys.stdout)


def exit(
    code: int = 0,
    *,
    text: str | None = None,
    output: HookOutput | dict[str, Any] | None = None,
    decision: PermissionDecision | None = None,
    reason: str | None = None,
    updated_input: dict[str, Any] | None = None,
    suppress_output: bool = True,
    to_stderr: bool = False,
    hook_event_name: HookEventName | None = None,
) -> NoReturn:
    """Exit hook with optional output or permission decision.

    This is the primary API for ending a hook. It handles both:
    - Permission decisions (decision, reason, updated_input, suppress_output)
    - Text/structured output (text, output, to_stderr)

    Args:
        code: Exit code (0 for success)
        text: Plain text to output
        output: Structured hook output
        decision: Permission decision ("allow", "deny", "ask")
        reason: Reason for permission decision
        updated_input: Modified tool input (for allow decisions)
        suppress_output: Suppress tool output in UI (default True for decisions)
        to_stderr: Send text to stderr instead of stdout
    """
    if decision is not None:
        _emit(
            decision=decision,
            reason=reason,
            updated_input=updated_input,
            suppress_output=suppress_output,
            hook_event_name=hook_event_name,
        )
    elif output is not None or text is not None:
        _emit(
            text=text,
            output=output,
            to_stderr=to_stderr,
            hook_event_name=hook_event_name,
        )
    sys.exit(code)
