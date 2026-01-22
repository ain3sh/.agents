"""Utilities for Factory Droid hooks.

This package provides common utilities for building Droid hooks:

- types: Typed dataclasses for hook input/output schemas
- io: Unified stdin parsing and stdout emission
- env: DROID_ENV_FILE helpers for persistent env vars
- config: Environment variable parsing helpers
- tokens: Token counting with tiktoken
- clipboard: Cross-platform clipboard operations

Example usage:

    from hooks.utils import (
        read_input_as,
        UserPromptSubmitInput,
        exit,
        count_tokens,
        env_bool,
        env_int,
    )

    def main():
        input = read_input_as(UserPromptSubmitInput)

        if env_bool("STRICT_MODE") and count_tokens(input.prompt) > env_int("MAX_TOKENS", 1000):
            exit(output={"decision": "block", "reason": "Prompt too long"})

        exit(text=f"Processing prompt with {count_tokens(input.prompt)} tokens")

    if __name__ == "__main__":
        main()
"""

# Types
from .types import (
    # Event types
    HookEventName,
    PermissionMode,
    PreCompactTrigger,
    SessionStartSource,
    SessionEndReason,
    PermissionDecision,
    BlockDecision,
    # Input types
    BaseHookInput,
    PreToolUseInput,
    PostToolUseInput,
    NotificationInput,
    UserPromptSubmitInput,
    StopInput,
    SubagentStopInput,
    PreCompactInput,
    SessionStartInput,
    SessionEndInput,
    HookInput,
    # Output types
    HookSpecificOutput,
    PreToolUseOutput,
    PostToolUseOutput,
    UserPromptSubmitOutput,
    SessionStartOutput,
    HookOutput,
    # Convenience types
    BlockResult,
    AllowResult,
    PermissionResult,
)

# I/O
from .io import HookInputError, read_input, read_input_as, exit

# Environment
from .env import (
    get_droid_env_file,
    set_env,
    set_envs,
    add_to_path,
    source_file,
    activate_venv,
    get_project_dir,
    get_plugin_root,
    is_droid_context,
)

# Config
from .config import (
    env_str,
    env_bool,
    env_int,
    env_float,
    env_path,
    env_list,
    env_set,
    env_choice,
    require_env,
    read_toml,
    load_toml,
    get_toml_section,
)

# Tokens
from .tokens import (
    count_tokens,
    count_tokens_exact,
    is_tiktoken_available,
    estimate_tokens,
    exceeds_threshold,
)

# Clipboard
from .clipboard import (
    copy_to_clipboard,
    get_from_clipboard,
    is_clipboard_available,
    is_wsl,
    is_macos,
    is_windows,
    is_linux,
)

__all__ = [
    # Types - Event types
    "HookEventName",
    "PermissionMode",
    "PreCompactTrigger",
    "SessionStartSource",
    "SessionEndReason",
    "PermissionDecision",
    "BlockDecision",
    # Types - Input types
    "BaseHookInput",
    "PreToolUseInput",
    "PostToolUseInput",
    "NotificationInput",
    "UserPromptSubmitInput",
    "StopInput",
    "SubagentStopInput",
    "PreCompactInput",
    "SessionStartInput",
    "SessionEndInput",
    "HookInput",
    # Types - Output types
    "HookSpecificOutput",
    "PreToolUseOutput",
    "PostToolUseOutput",
    "UserPromptSubmitOutput",
    "SessionStartOutput",
    "HookOutput",
    # Types - Convenience types
    "BlockResult",
    "AllowResult",
    "PermissionResult",
    # I/O
    "HookInputError",
    "read_input",
    "read_input_as",
    "exit",
    # Environment
    "get_droid_env_file",
    "set_env",
    "set_envs",
    "add_to_path",
    "source_file",
    "activate_venv",
    "get_project_dir",
    "get_plugin_root",
    "is_droid_context",
    # Config
    "env_str",
    "env_bool",
    "env_int",
    "env_float",
    "env_path",
    "env_list",
    "env_set",
    "env_choice",
    "require_env",
    "read_toml",
    "load_toml",
    "get_toml_section",
    # Tokens
    "count_tokens",
    "count_tokens_exact",
    "is_tiktoken_available",
    "estimate_tokens",
    "exceeds_threshold",
    # Clipboard
    "copy_to_clipboard",
    "get_from_clipboard",
    "is_clipboard_available",
    "is_wsl",
    "is_macos",
    "is_windows",
    "is_linux",
]
