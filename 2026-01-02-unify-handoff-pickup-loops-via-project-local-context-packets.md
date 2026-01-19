## Goals
- Create a harness-agnostic, project-local “context system” rooted at `./.agent/context/`.
- Keep the richer `/handoff` output while adding (a) a focused “next prompt” extract (Amp-style) and (b) optional iteration semantics (Ralph-style).
- Support **multiple loop definitions**, while keeping behavior user-controlled (no blocking).
- Maintain **both** relevant-files sources: auto-suggested + user-curated.

## Non-goals (for v1)
- No forced workflow (no hard blocks); hooks only help/iterate.
- No transcript rewriting or checkpointing (that’s `rewind`’s domain).
- No new UI; everything is artifacts + slash-commands + optional hooks.

## Canonical Project Layout (single source of truth)
All state lives under the session’s project root:
- `./.agent/context/`
  - `root.json` — marker + metadata used for root discovery
  - `packets/` — handoffs/pickups/work packets
  - `loops/` — loop definitions/state
  - `indexes/` — lightweight indexes for discovery
  - `scratch/` — transient helper data (optional)

### Root discovery rule
Given any `cwd`, find the nearest ancestor containing `./.agent/context/root.json`. If missing:
- Soft-fallback to git root (if present) then `cwd`.
- Provide `/context init` to create the marker explicitly.
- SessionStart hook (optional) can auto-create it.

## Canonical Artifact: Context Packet (`./.agent/context/packets/<ts>-<slug>.md`)
A single markdown file with minimal frontmatter + rich sections.

### Frontmatter (line-oriented YAML-like; no complex nesting)
Required:
- `id`: stable string (e.g. `<ts>-<slug>`)
- `created_at`, `updated_at`: ISO8601 UTC
- `status`: `draft|active|done|blocked`
- `purpose`: short user goal
Optional:
- `source`: `factory|claude|unknown`
- `session_id`, `transcript_path` (best-effort)
- `relevant_files_confirmed`: JSON array string
- `relevant_files_suggested`: JSON array string
- `validators`: JSON array string
- `loop_promise`: string or null
- `loop_max_iterations`: int or 0

### Body sections (keep richer)
Suggested canonical headings (order matters for tooling):
1. `## Intent`
2. `## Context`
3. `## Constraints`
4. `## Decisions`
5. `## Relevant Files`
   - `### Confirmed`
   - `### Suggested`
6. `## Next Prompt (Draft)`  ← the Amp-style extract
7. `## Plan`
8. `## Validators / Exit Criteria`
9. `## Open Questions`
10. `## Notes`

### Packet lifecycle
- `/handoff <purpose>` creates a new packet (status `draft`) with a filled “Next Prompt (Draft)” and both relevant-file lists.
- `/pickup <id>` renders a prompt **from the packet**, but does not mutate it by default.
- `/packet activate <id>` sets status `active` and updates `updated_at`.

## Loops: Multi-loop Support Without Chaos
Because a Stop hook can only “continue one thing” at a time, we support **multiple loop artifacts**, but only one is “foreground” per session.

### Loop artifact (`./.agent/context/loops/<loop-id>.md`)
Frontmatter:
- `id`, `created_at`, `updated_at`
- `status`: `active|paused|done|cancelled`
- `iteration`: int
- `max_iterations`: int or 0
- `completion_promise`: string or null
- `source_packet_id`: optional
Body:
- `## Loop Prompt` (verbatim)
- `## Notes`

### Foreground selection
- `./.agent/context/indexes/active-loop.json` contains `{ "active_loop_id": "..." }`.
- Starting a loop sets it active. Switching loops is explicit (`/loop activate <id>`).

## Relevant Files: “Both” Source of Truth
- **Suggested**: automatically collected via PostToolUse/PreToolUse (paths the agent touched or referenced).
- **Confirmed**: explicitly curated inside the packet.

Storage approach:
- Append-only log: `./.agent/context/indexes/relevant-files.jsonl` with entries `{timestamp, file_path, source: tool|user, packet_id?, confidence}`.
- Packet command compaction: `/handoff` snapshots current suggested set into the packet.

## Slash Commands (minimal surface)
### Core
- `/context init` — create `./.agent/context/root.json` + indexes skeleton.
- `/handoff <purpose>` — generate packet with rich sections + “Next Prompt (Draft)”.
- `/pickup <packet-id>` — output a structured prompt that references the packet + its relevant files.

### Packet utilities
- `/packet list` — list packets (by `updated_at`).
- `/packet open <id>` — print path (or open in editor if supported).
- `/packet activate <id>` — set status `active`.

### Loop utilities
- `/loop start <prompt|--from-packet ID> [--max-iterations N] [--promise TEXT]` — create loop md + set foreground.
- `/loop list` — list loops and statuses.
- `/loop activate <id>` — set foreground loop.
- `/loop pause <id>` / `/loop resume <id>`
- `/loop cancel <id>`

## Hooks (optional, non-blocking)
### SessionStart hook (recommended)
- Ensure root marker exists.
- Record best-effort session metadata in `./.agent/context/root.json` and/or `./.agent/context/indexes/sessions.jsonl`.
- Emit context guidance only (no decisions enforced).

### Stop hook (loop engine)
- If `active-loop.json` points to an `active` loop:
  - Parse last assistant message for `<promise>…</promise>`.
  - If matches promise → mark loop done, clear active pointer, allow Stop.
  - Else increment iteration, check max-iterations, then **block** Stop with the same `Loop Prompt`.
- If no active loop → allow Stop.

### PostToolUse hook (file suggestion collector)
- On file-modifying tools, append touched file paths into `relevant-files.jsonl` as `suggested`.
- Never blocks; best-effort logging only.

## Integration points (Factory + Claude)
- Use the same artifact format and root discovery everywhere.
- Keep agent-specific differences behind adapters (how to extract transcript path, how Stop hook re-injects prompt, etc.).

## Migration mapping from what exists today
- `~/.factory/commands/handoff.md` → becomes `/handoff` but writes packets into `./.agent/context/packets/`.
- `~/.factory/commands/pickup.md` → becomes `/pickup` reading packets.
- Ralph plugin’s `.claude/ralph-loop.local.md` → replaced by `./.agent/context/loops/*.md` + `active-loop.json`.

## Acceptance criteria
- From any subdirectory, commands locate the same project root via `./.agent/context/root.json`.
- `/handoff` produces a packet that is both human-usable (rich) and machine-usable (“Next Prompt”, validators, file lists).
- Multiple loops can exist; switching the foreground loop is explicit and deterministic.
- Hooks never force behavior beyond loop continuation when the user started a loop.

## Open questions (small)
- Should `root.json` store a stable `project_id` (uuid) to disambiguate similar trees?
- Do you want loop completion to accept multiple promises (e.g. `DONE|BLOCKED`), or keep single exact match?
- Should `/pickup` optionally “hydrate” suggested files by re-scanning tool logs, or only use what’s in the packet?