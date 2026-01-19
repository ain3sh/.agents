---
name: droid-exec
description: Spawn focused subagent tasks via `droid exec`. Use for parallel processing, isolated operations, or delegating work that benefits from fresh context.
---

# Droid Exec Subagent Spawning

## When to Use

Spawn a subagent when:
- Task is **isolated** (doesn't need your current context)
- Task can run **in parallel** with your work
- Task benefits from **fresh context window** (large file processing)
- You need **different model characteristics** (speed vs reasoning)

Do NOT spawn when:
- Task requires your conversation context
- You need to iterate interactively on results
- Simple operation you can do directly

## Invocation

```bash
droid exec [options] "<prompt>"
```

### Async Execution (Fire-and-Forget)

To spawn without blocking, use the `fireAndForget` parameter in your Execute tool call:

```json
{
  "command": "droid exec --auto low \"<task>\"",
  "fireAndForget": true
}
```

The subagent runs independently. Check results via output files or session continuation.

## Autonomy Levels

| Flag | Allows | Blocks | Use For |
|------|--------|--------|---------|
| *(none)* | Read-only: cat, ls, git status/diff/log | All writes | Analysis, planning |
| `--auto low` | File create/edit in project | System changes, installs | Code mods, docs |
| `--auto medium` | + npm/pip install, build, test, git commit | git push, sudo | Dev workflows |
| `--auto high` | + git push, deploy, network ops | sudo rm -rf / | CI/CD, deploys |

⚠️ `--skip-permissions-unsafe` — Only in disposable containers. Bypasses ALL checks.

## Output Formats

### For Human Consumption (default)
```bash
droid exec "summarize changes"
```

### For Programmatic Parsing
```bash
result=$(droid exec --output-format json "analyze deps")
# Returns: {"type":"result","subtype":"success","result":"...","session_id":"...","duration_ms":...}

# Extract fields:
message=$(echo "$result" | jq -r '.result')
session=$(echo "$result" | jq -r '.session_id')
```

### For Real-Time Monitoring
```bash
droid exec --output-format stream-json "complex task" | while IFS= read -r line; do
  case $(echo "$line" | jq -r '.type') in
    tool_call) echo "Tool: $(echo "$line" | jq -r '.toolName')" ;;
    completion) echo "Done: $(echo "$line" | jq -r '.finalText')" ;;
  esac
done
```

## Model Selection

```bash
droid exec -m claude-sonnet-4-5-20250929 "fast task"      # Speed
droid exec -m claude-opus-4-5-20251101 "complex task"     # Default, high capability
droid exec -m gpt-5.1-codex "coding task"                 # Alternative
```

### Custom Models

Custom models are configured in `~/.factory/settings.json` under `customModels`:

```json
{
  "customModels": [
    {
      "model": "gemini-3-flash-preview",
      "displayName": "google://gemini-3-flash",
      "baseUrl": "http://127.0.0.1:8317/v1",
      "apiKey": "your-key",
      "provider": "openai"
    }
  ]
}
```

Reference as `custom:<displayName-with-dashes>-<index>`:
```bash
droid exec -m "custom:google://gemini-3-flash-2" "task"
```

### Reasoning Effort

```bash
droid exec -r high "complex reasoning task"   # More thinking
droid exec -r low "simple task"               # Faster
```

## Effective Prompts

### Pattern 1: Concrete Before/After Examples
```bash
droid exec --auto low "
Fix error messages to be user-friendly.

BEFORE: throw new Error('EINVAL');
AFTER:  throw new Error('Invalid email format. Example: user@domain.com');

Apply to all files in src/errors/
"
```

### Pattern 2: Explicit Steps + Constraints
```bash
droid exec --auto low "
1. Find all .ts files in src/ missing JSDoc
2. Add @param and @return tags
3. Preserve existing code exactly
4. Write summary to jsdoc-report.md
"
```

### Pattern 3: Artifact Output
```bash
droid exec --auto low "Analyze dependencies and write findings to deps-analysis.json"
```

Always request file output for results you need to process.

## Session Continuation

```bash
# Start task, capture session
result=$(droid exec --output-format json "begin auth refactor")
session=$(echo "$result" | jq -r '.session_id')

# Continue with context
droid exec -s "$session" "now add tests for the refactored code"
```

## Parallel Execution

```bash
# Process files concurrently
find src -name "*.ts" -print0 | xargs -0 -P 4 -I {} \
  droid exec --auto low "Modernize {}"

# Background jobs
for pkg in packages/*; do
  droid exec --cwd "$pkg" --auto low "Run lint and write report.md" &
done
wait
```

## Scoping

```bash
droid exec --cwd packages/auth "analyze this module"  # Constrain to directory
```

## Tool Control

```bash
droid exec --list-tools                              # See available tools
droid exec --enabled-tools ApplyPatch,Read "task"    # Whitelist
droid exec --disabled-tools execute-cli "task"       # Blacklist
```

## Spec Mode

Plan before executing:
```bash
droid exec --use-spec --auto low "refactor auth module"
droid exec --use-spec --spec-model claude-haiku-4-5-20251001 --auto medium "implement feature"
```

## Error Handling

```bash
if ! result=$(droid exec --auto low "risky operation" 2>&1); then
  echo "Failed: $result" >&2
  exit 1
fi
```

Exit codes: 0 = success, non-zero = failure (permission violation, tool error, unmet objective)

## Quick Decision Matrix

| Need | Approach |
|------|----------|
| Analyze without changes | `droid exec "..."` |
| Edit files | `droid exec --auto low "..."` |
| Build/test workflow | `droid exec --auto medium "..."` |
| Push/deploy | `droid exec --auto high "..."` |
| Parse results | `--output-format json` |
| Don't wait for completion | `fireAndForget: true` in Execute |
| Continue previous work | `-s <session-id>` |
| Scope to directory | `--cwd /path` |
| Different model | `-m <model-id>` |
| More reasoning | `-r high` |
