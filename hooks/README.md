# Agent Hooks

Reusable Python utilities and hooks for Factory Droid, Claude Code, etc.. The `utils/` library handles JSON parsing, output emission, env vars, and common operations—so hooks can focus on logic, not plumbing.

## Directory Layout

```
hooks/
├── utils/                  # Shared utilities
│   ├── types.py            # Typed dataclasses for all hook inputs/outputs
│   ├── io.py               # Stdin parsing, stdout emission, exit helpers
│   ├── config.py           # Environment variable parsing (env_bool, env_int, etc.)
│   ├── env.py              # DROID_ENV_FILE helpers (set_env, add_to_path)
│   ├── tokens.py           # Token counting (tiktoken with fallback)
│   └── clipboard.py        # Cross-platform clipboard operations
├── env_vars.py             # SessionStart: loads ~/.factory/vars.env
├── prompt_conflict_identifier.py  # UserPromptSubmit: blocks long prompts
└── pre_compact.py          # PreCompact: logs compaction events
```

## Quick Start

Minimal hook example—a `PreToolUse` hook that denies `rm -rf /`:

```python
#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from utils import read_input_as, PreToolUseInput, emit_permission_deny, exit_success

def main():
    inp = read_input_as(PreToolUseInput)
    
    if inp.tool_name == "Bash" and "rm -rf /" in inp.tool_input.get("command", ""):
        emit_permission_deny("Blocked: dangerous command")
        return
    
    exit_success()

if __name__ == "__main__":
    main()
```

## Utils Reference

### I/O (`utils.io`)

| Function | Description |
|----------|-------------|
| `read_input()` | Parse stdin JSON, auto-detect hook type, return typed input |
| `read_input_as(Type)` | Parse stdin JSON, validate it matches `Type` |
| `emit_block(reason)` | Output `{"decision": "block", "reason": ...}` |
| `emit_context(msg)` | Print context (for UserPromptSubmit/SessionStart) |
| `emit_permission_allow(reason)` | PreToolUse: allow and bypass permission system |
| `emit_permission_deny(reason)` | PreToolUse: deny tool call, reason shown to Droid |
| `emit_permission_ask(reason)` | PreToolUse: prompt user to confirm |
| `emit_modified_input(updates)` | PreToolUse: allow with modified tool input |
| `exit_success()` | Exit 0 (allow) |
| `exit_block(msg)` | Exit 2, stderr shown to Droid |
| `exit_error(msg)` | Exit 1, stderr shown to user |

### Input Types (`utils.types`)

| Type | Hook Event | Key Fields |
|------|------------|------------|
| `PreToolUseInput` | PreToolUse | `tool_name`, `tool_input` |
| `PostToolUseInput` | PostToolUse | `tool_name`, `tool_input`, `tool_response` |
| `UserPromptSubmitInput` | UserPromptSubmit | `prompt` |
| `NotificationInput` | Notification | `message` |
| `StopInput` | Stop | `stop_hook_active` |
| `SubagentStopInput` | SubagentStop | `stop_hook_active` |
| `PreCompactInput` | PreCompact | `trigger`, `custom_instructions` |
| `SessionStartInput` | SessionStart | `source` |
| `SessionEndInput` | SessionEnd | `reason` |

All inputs share: `session_id`, `transcript_path`, `cwd`, `permission_mode`, `hook_event_name`

### Config (`utils.config`)

```python
from utils import env_bool, env_int, env_str, env_path, env_list

debug = env_bool("DEBUG", False)           # Parses 1/true/yes/on
threshold = env_int("THRESHOLD", 1000)     # Int with fallback
api_url = env_str("API_URL", "localhost")  # String with fallback
data_dir = env_path("DATA_DIR", "/tmp")    # Returns Path object
tags = env_list("TAGS", sep=",")           # Splits "a,b,c" → ["a","b","c"]
```

### Environment (`utils.env`)

```python
from utils import set_env, add_to_path, activate_venv, get_project_dir

# Persist env vars for Droid session (writes to DROID_ENV_FILE)
set_env("MY_VAR", "value")
add_to_path("/usr/local/bin")
activate_venv("./venv")

# Read Droid context
project = get_project_dir()  # FACTORY_PROJECT_DIR as Path
```

### Tokens (`utils.tokens`)

```python
from utils import count_tokens, exceeds_threshold

tokens = count_tokens("Hello world")  # Uses tiktoken, falls back to len/4
if exceeds_threshold(long_text, 2000):
    emit_block("Too long")
```

### Clipboard (`utils.clipboard`)

```python
from utils import copy_to_clipboard, is_wsl, is_macos

if copy_to_clipboard("/check-conflicts"):
    print("Copied!")
```

Works on macOS (pbcopy), Windows (clip.exe), WSL, Linux (xclip/xsel).

## Existing Hooks

### `env_vars.py`
**Event:** SessionStart (startup only)  
**Purpose:** Loads `~/.factory/vars.env` into the Droid session. Provides Claude Code-like `"env": {}` UX.

### `prompt_conflict_identifier.py`
**Event:** UserPromptSubmit  
**Purpose:** Blocks prompts exceeding token threshold, saves to `/tmp/prompt-conflicts/`, copies `/check-conflicts` to clipboard.  
**Config:** `LONG_PROMPT_THRESHOLD`, `PROMPT_CONFLICT_ALWAYS_ON`, `PROMPT_CONFLICT_ALLOW_OVERRIDE`

### `pre_compact.py`
**Event:** PreCompact  
**Purpose:** Logs manual/auto compaction events with any custom instructions.

## Configuration

### `~/.factory/vars.env`

Environment variables loaded on session start:

```bash
# Hook config
LONG_PROMPT_THRESHOLD=2000
PROMPT_CONFLICT_ALLOW_OVERRIDE=true

# Custom vars
MY_API_KEY=secret
```

### `~/.factory/settings.json`

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup",
        "hooks": [
          { "type": "command", "command": "~/.factory/hooks/env_vars.py", "timeout": 5 }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [
          { "type": "command", "command": "~/.factory/hooks/prompt_conflict_identifier.py", "timeout": 30 }
        ]
      }
    ]
  }
}
```

## See Also

- [Factory Hooks Reference](https://docs.factory.ai/reference/hooks-reference) — Full hook API docs for Factory Droid
- [Claude Code Hooks Reference](https://code.claude.com/docs/en/hooks.md) — Full hook API docs for Claude Code
- [Session Automation Guide](https://docs.factory.ai/guides/hooks/session-automation) — Droid session configuration example
