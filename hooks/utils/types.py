"""Type definitions for Factory Droid hooks.

This module provides typed dataclasses for all hook input/output schemas,
based on the official Factory hooks reference documentation.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Literal

# ============================================================================
# Hook Event Types
# ============================================================================

HookEventName = Literal[
    "PreToolUse",
    "PostToolUse",
    "Notification",
    "UserPromptSubmit",
    "Stop",
    "SubagentStop",
    "PreCompact",
    "SessionStart",
    "SessionEnd",
]

PermissionMode = Literal["default", "plan", "acceptEdits", "bypassPermissions"]

# PreCompact triggers
PreCompactTrigger = Literal["manual", "auto"]

# SessionStart sources
SessionStartSource = Literal["startup", "resume", "clear", "compact"]

# SessionEnd reasons
SessionEndReason = Literal["clear", "logout", "prompt_input_exit", "other"]

# PreToolUse permission decisions
PermissionDecision = Literal["allow", "deny", "ask"]

# Block decision (for PostToolUse, UserPromptSubmit, Stop, SubagentStop)
BlockDecision = Literal["block"]


# ============================================================================
# Base Hook Input
# ============================================================================

@dataclass(slots=True)
class BaseHookInput:
    """Common fields present in all hook inputs."""

    session_id: str
    transcript_path: str
    cwd: str
    permission_mode: PermissionMode
    hook_event_name: HookEventName


# ============================================================================
# Event-Specific Hook Inputs
# ============================================================================

@dataclass(slots=True)
class PreToolUseInput(BaseHookInput):
    """Input for PreToolUse hooks."""

    tool_name: str
    tool_input: dict[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "hook_event_name", "PreToolUse")


@dataclass(slots=True)
class PostToolUseInput(BaseHookInput):
    """Input for PostToolUse hooks."""

    tool_name: str
    tool_input: dict[str, Any]
    tool_response: dict[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "hook_event_name", "PostToolUse")


@dataclass(slots=True)
class NotificationInput(BaseHookInput):
    """Input for Notification hooks."""

    message: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "hook_event_name", "Notification")


@dataclass(slots=True)
class UserPromptSubmitInput(BaseHookInput):
    """Input for UserPromptSubmit hooks."""

    prompt: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "hook_event_name", "UserPromptSubmit")


@dataclass(slots=True)
class StopInput(BaseHookInput):
    """Input for Stop hooks."""

    stop_hook_active: bool

    def __post_init__(self) -> None:
        object.__setattr__(self, "hook_event_name", "Stop")


@dataclass(slots=True)
class SubagentStopInput(BaseHookInput):
    """Input for SubagentStop hooks."""

    stop_hook_active: bool

    def __post_init__(self) -> None:
        object.__setattr__(self, "hook_event_name", "SubagentStop")


@dataclass(slots=True)
class PreCompactInput(BaseHookInput):
    """Input for PreCompact hooks."""

    trigger: PreCompactTrigger
    custom_instructions: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "hook_event_name", "PreCompact")


@dataclass(slots=True)
class SessionStartInput(BaseHookInput):
    """Input for SessionStart hooks."""

    source: SessionStartSource

    def __post_init__(self) -> None:
        object.__setattr__(self, "hook_event_name", "SessionStart")


@dataclass(slots=True)
class SessionEndInput(BaseHookInput):
    """Input for SessionEnd hooks."""

    reason: SessionEndReason

    def __post_init__(self) -> None:
        object.__setattr__(self, "hook_event_name", "SessionEnd")


# Union type for all hook inputs
HookInput = (
    PreToolUseInput
    | PostToolUseInput
    | NotificationInput
    | UserPromptSubmitInput
    | StopInput
    | SubagentStopInput
    | PreCompactInput
    | SessionStartInput
    | SessionEndInput
)


# ============================================================================
# Hook Output Types
# ============================================================================

@dataclass(slots=True)
class HookSpecificOutput:
    """Base for hook-specific output fields."""

    hook_event_name: HookEventName = field(init=False, default="PreToolUse")


@dataclass(slots=True)
class PreToolUseOutput(HookSpecificOutput):
    """PreToolUse-specific output fields."""

    permission_decision: PermissionDecision | None = None
    permission_decision_reason: str | None = None
    updated_input: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "hook_event_name", "PreToolUse")

    def to_dict(self) -> dict[str, Any]:
        """Convert to JSON-serializable dict with camelCase keys."""
        result: dict[str, Any] = {"hookEventName": self.hook_event_name}
        if self.permission_decision is not None:
            result["permissionDecision"] = self.permission_decision
        if self.permission_decision_reason is not None:
            result["permissionDecisionReason"] = self.permission_decision_reason
        if self.updated_input is not None:
            result["updatedInput"] = self.updated_input
        return result


@dataclass(slots=True)
class PostToolUseOutput(HookSpecificOutput):
    """PostToolUse-specific output fields."""

    additional_context: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "hook_event_name", "PostToolUse")

    def to_dict(self) -> dict[str, Any]:
        """Convert to JSON-serializable dict with camelCase keys."""
        result: dict[str, Any] = {"hookEventName": self.hook_event_name}
        if self.additional_context is not None:
            result["additionalContext"] = self.additional_context
        return result


@dataclass(slots=True)
class UserPromptSubmitOutput(HookSpecificOutput):
    """UserPromptSubmit-specific output fields."""

    additional_context: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "hook_event_name", "UserPromptSubmit")

    def to_dict(self) -> dict[str, Any]:
        """Convert to JSON-serializable dict with camelCase keys."""
        result: dict[str, Any] = {"hookEventName": self.hook_event_name}
        if self.additional_context is not None:
            result["additionalContext"] = self.additional_context
        return result


@dataclass(slots=True)
class SessionStartOutput(HookSpecificOutput):
    """SessionStart-specific output fields."""

    additional_context: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "hook_event_name", "SessionStart")

    def to_dict(self) -> dict[str, Any]:
        """Convert to JSON-serializable dict with camelCase keys."""
        result: dict[str, Any] = {"hookEventName": self.hook_event_name}
        if self.additional_context is not None:
            result["additionalContext"] = self.additional_context
        return result


@dataclass(slots=True)
class HookOutput:
    """Complete hook output structure.

    This represents the full JSON output a hook can return.
    """

    # Common fields
    decision: BlockDecision | None = None
    reason: str | None = None
    continue_: bool | None = None  # 'continue' is reserved in Python
    stop_reason: str | None = None
    system_message: str | None = None

    # Hook-specific output
    hook_specific_output: (
        PreToolUseOutput
        | PostToolUseOutput
        | UserPromptSubmitOutput
        | SessionStartOutput
        | None
    ) = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to JSON-serializable dict with camelCase keys."""
        result: dict[str, Any] = {}

        if self.decision is not None:
            result["decision"] = self.decision
        if self.reason is not None:
            result["reason"] = self.reason
        if self.continue_ is not None:
            result["continue"] = self.continue_
        if self.stop_reason is not None:
            result["stopReason"] = self.stop_reason
        if self.system_message is not None:
            result["systemMessage"] = self.system_message
        if self.hook_specific_output is not None:
            result["hookSpecificOutput"] = self.hook_specific_output.to_dict()

        return result


# ============================================================================
# Convenience Type Aliases
# ============================================================================

# For hooks that can block (PostToolUse, UserPromptSubmit, Stop, SubagentStop)
@dataclass(slots=True, frozen=True)
class BlockResult:
    """Result indicating a hook wants to block an action."""

    reason: str


@dataclass(slots=True, frozen=True)
class AllowResult:
    """Result indicating a hook allows an action to proceed."""

    context: str | None = None  # Additional context to inject


# For PreToolUse permission decisions
@dataclass(slots=True, frozen=True)
class PermissionResult:
    """Result for PreToolUse permission decision."""

    decision: PermissionDecision
    reason: str | None = None
    updated_input: dict[str, Any] | None = None
