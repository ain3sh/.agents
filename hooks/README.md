# Agent Hooks

High-level, reusable hooks for Factory Droid that prioritize clear behavior, reliable defaults, and minimal boilerplate. This repository is the one-stop reference for how hooks are organized, how they’re configured, and how to extend them without re-reading the codebase.

## At a Glance

- **Hooks are grouped by event** (`pre_tool_use/`, `session_start/`, etc.).
- **Utilities live in `utils/`**, providing typed I/O, env helpers, and cross-platform tools.
- **Configuration lives outside this repo** (behavior in `~/.agents/configs/droid.toml`).

## Directory Layout

```
hooks/
├── utils/
│   ├── __init__.py
│   ├── types.py
│   ├── io.py
│   ├── config.py
│   ├── env.py
│   ├── tokens.py
│   └── clipboard.py
├── pre_tool_use/
│   ├── policy.py
│   └── commit_review_guard.py
├── post_tool_use/
│   └── instructions.py
├── pre_compact/
│   ├── block_auto.py
│   └── instructions.py
├── session_start/
│   ├── env_vars.py
│   ├── instructions.py
│   └── debug.sh
├── session_end/
│   └── store_artifacts.py
└── user_prompt_submit/
    └── conflict_guard.py
```

## Quick Start (Minimal Hook)

Example `PreToolUse` hook that blocks dangerous commands:

```python
#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils import HookInputError, PreToolUseInput, exit, read_input_as  # type: ignore


def main() -> None:
    try:
        hook_input = read_input_as(PreToolUseInput)
    except HookInputError as exc:
        exit(1, text=f"[example] Hook input error: {exc}", to_stderr=True)

    if hook_input.tool_name == "Bash" and "rm -rf /" in str(hook_input.tool_input.get("command", "")):
        exit(decision="deny", reason="Blocked: dangerous command")

    exit()


if __name__ == "__main__":
    main()
```

## Utilities (What You Should Use)

### `utils.io`
- `read_input()` and `read_input_as(...)` parse stdin into typed inputs.
- `emit(...)` sends hook output (permission decisions, additional context, etc.).
- `exit(...)` exits with optional output or error text.

### `utils.instructions`
- Shared instruction rendering for SessionStart/PostToolUse.
- Supports `include` + `include_text` with `${...}` interpolation.
- Soft-warns on unresolved/ambiguous placeholders (stderr), but never blocks.

### `utils.types`
- Typed dataclasses for **all hook inputs/outputs**, plus helper types like `PermissionResult`.
- Use `PreToolUseInput`, `SessionStartInput`, etc. to avoid stringly-typed code.

### `utils.config`
- Typed env parsing: `env_bool`, `env_int`, `env_float`, `env_path`, `env_list`, `env_set`, `env_choice`, `require_env`.
- TOML helpers: `read_toml`, `load_toml`, `get_toml_section`.

### `utils.env`
- Persist env vars via `DROID_ENV_FILE` using `set_env`/`set_envs`.
- Session helpers: `get_project_dir`, `get_plugin_root`, `is_droid_context`.

### `utils.tokens`
- Token counts with tiktoken when available (`count_tokens`, `count_tokens_exact`).
- Fast heuristics and threshold checks (`estimate_tokens`, `exceeds_threshold`).

### `utils.clipboard`
- Cross-platform clipboard access: `copy_to_clipboard`, `get_from_clipboard`.
- Platform detection: `is_wsl`, `is_macos`, `is_windows`, `is_linux`.

## Hook Catalog (Behavior Summary)

### PreToolUse
- **`policy.py`**: rule-based tool policy with glob matching and `server:tool` pattern matching. Supports allow, ask, or deny decisions.
- **`commit_review_guard.py`**: blocks `git push` if CodeRabbit CLI reports findings; runs on detected push commands.

### PostToolUse
- **`instructions.py`**: rule-based instruction injection by tool, with optional input/output matching (string, regex, or structured dict) and `${...}` interpolation for dynamic text.

### PreCompact
- **`block_auto.py`**: prevents auto-compaction while allowing manual `/compact`.
- **`instructions.py`**: injects default compaction instructions from `commands/compact.md` when manual compact has none.

### SessionStart
- **`env_vars.py`**: loads inline config env vars plus optional secrets file on `startup`, `resume`, and `clear`.
- **`instructions.py`**: injects instructions via ordered rules (`when` + `include`/`include_text`) with interpolation support.
- **`debug.sh`**: emits detailed diagnostics for env discovery and tool availability.

### SessionEnd
- **`store_artifacts.py`**: stores session tail and latest todos under `.agents/{MM_DD_YYYY}/`.

### UserPromptSubmit
- **`conflict_guard.py`**: blocks long prompts, stores them on disk, and instructs use of `/check-conflicts`.

## Configuration

### `~/.agents/configs/droid.toml` (Behavior)

```toml
[hooks.session_start.environment]
when = ["startup", "resume", "clear"]
secrets = "~/.factory/.env"
EXAMPLE_CONFIG_VAR = "clod"

[hooks.session_start.instructions]
prompts_dir = "~/.agents/prompts"
[[hooks.session_start.instructions.rules]]
when = ["startup", "clear"]
include = ["instructions/OPERATOR.md"]
[[hooks.session_start.instructions.rules]]
when = ["compact"]
include = ["instructions/POST_COMPACT.md"]
[[hooks.session_start.instructions.rules]]
when = ["*"]
include = ["instructions/PRINCIPLES.md"]

[hooks.post_tool_use.instructions]
prompts_dir = "~/.agents/prompts"
debug = false

[[hooks.post_tool_use.instructions.rules]]
match.tool = "ExitSpecMode"
match.output = { approved = true, isEdited = true }
include = ["instructions/IMPLEMENT_SPEC.md"]
include_text = ["Read ${filePath} fully to make a mental note of all changes made first."]

[hooks.pre_tool_use.policy]
[hooks.pre_tool_use.policy.allow]
tools = ["codebase:warpgrep_*"]
message = "[policy] {tool_name} is allowlisted"

[hooks.user_prompt_submit.conflict_guard]
cache_dir = "/tmp/conflicts"
token_threshold = 20000
skip_prefix = ""

[hooks.session_end.store_artifacts]
tail = 1
tail_when = ["prompt_input_exit", "other"]
todo_when = ["prompt_input_exit", "clear", "other"]
```


## Operating Model (How These Hooks Fit Together)

1. **SessionStart** loads defaults and optional env vars.
2. **UserPromptSubmit** can block overly long prompts and route them for analysis.
3. **PreToolUse** enforces permissions and pre-flight checks (policy, CodeRabbit on push).
4. **PostToolUse** injects reminders after specific tool actions.
5. **PreCompact** governs compaction behavior and instructions.
6. **SessionEnd** stores run artifacts (tail + todo snapshot).

## Adding a New Hook (Minimal Checklist)

1. Create a script in the correct event directory.
2. Parse input with `read_input_as(...)` and handle errors.
3. Emit decisions or context with `exit(...)` and exit cleanly.
4. Register the hook in your runtime-specific configuration (matcher, command, timeout).

## Troubleshooting

- **Hook not firing:** verify your runtime hook registration (matcher, command, timeout).
- **Env vars not persisting:** ensure `DROID_ENV_FILE` or `CLAUDE_ENV_FILE` is set.
- **Need diagnostics:** run `session_start/debug.sh` to inspect env discovery.

## References

- Factory Hooks Reference: https://docs.factory.ai/reference/hooks-reference
- Claude Code Hooks: https://code.claude.com/docs/en/hooks.md
