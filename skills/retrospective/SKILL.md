---
name: retrospective
description: Self-review your aggregate diff before shipping to catch dead weight, junk code, perf misses, pattern drift, AI slop, and scope creep. Use when the user asks to scrub, stranger-review, or clean up changes prior to opening a PR.
argument-hint: [<base-ref>]
---

Take a beat. Reread what you just shipped as if a stranger wrote it. The bar is **entropy reduction**: leave the diff leaner, sharper, and more consistent than when you started. Every shortcut you leave here is someone else's burden later.

Load skills: **single-canon** (for legacy/fallback branches). If the session added or moved tests, also load **consolidate-test-suites**.

## Todo cadence (non-optional)

At every `##` boundary: prior → `completed`, incoming → `in_progress`. Every finding you plan to fix becomes its own todo before you edit.

## 1. Orient

Resolve the comparison base. Default is the remote default branch; override with `$ARGUMENTS`.

```bash
DEFAULT=$(git remote show origin 2>/dev/null | awk '/HEAD branch/ {print $NF}')
BASE="${1:-origin/$DEFAULT}"
git log --oneline "$BASE"..HEAD
git diff --stat "$BASE"..HEAD
```

State the **stated goal** of the change (from the ticket, PR description, or recent conversation) in one sentence. Hold it next to the **actual diff**. Scope creep is the first thing to catch.

## 2. Read whole files, not hunks

You cannot evaluate a helper's necessity, a name's clarity, or a pattern's fit from a 3-line window. For each modified file:

- Open it end-to-end — not just the changed hunks.
- Extra scrutiny on files with >3 hunks (consolidation usually hiding) and newly-created files (must earn their existence — would an existing module host this better?).
- Flag files you did not intend to touch (merge residue, accidental saves, auto-formatter spray) and revert those hunks.

## 3. Probe for entropy

Walk each category. Record every finding as a triage candidate — severity comes next.

### Dead weight

- Unused imports, unreferenced exports, orphaned helpers.
- Commented-out code, stray `console.log` / `print` / `dbg!`, `TODO`s without a ticket.
- Config knobs or feature flags added "for flexibility" with one real caller.
- Stale comments that contradict the code beneath.
- Types, interfaces, or enums with no consumer.

### Junk code

- Wrapper-over-wrapper with no added value. Inline.
- Defensive `try/catch` that swallows errors and returns `null` / `{}` / a default. Let it throw.
- Premature abstractions: generics / strategy / factory / adapter with exactly one implementation. Collapse.
- Duplicated logic across two new files. Unify.
- Local re-implementation of a helper that already exists — grep to confirm, then reuse.
- Legacy/fallback branches for state that never existed in the new schema — apply **single-canon** and delete.
- `any` / `unknown` / `Object` / `interface{}` leaks that mask a real type you know.

### Blatant optimization opportunities

- Sequential `await`s where the calls are independent → `Promise.all`.
- N+1: loops issuing one request per item.
- Redundant work inside a hot loop — hoist it.
- Accidental removal of memoization / caching / indexed access.
- Synchronous I/O on a per-request or startup path.
- Re-parsing or re-serializing the same payload more than once along a flow.

### Pattern drift

- New file that diverges from surrounding convention (naming, layout, error idiom).
- Local import-order or type-alias style deltas — usually a missed `format` run.
- Re-implementing something the codebase already provides as a canonical utility.
- Mixing paradigms mid-module (e.g., callbacks beside promises, classes beside pure functions) without reason.

### AI-slop signals (run `slop-scan`)

For any JS/TS diff, run `slop-scan delta <base-dir> <head-dir> --json` on temp dirs holding only the changed files (`delta` takes directory paths, not git refs — build them with the changed-files recipe in the **quality-ship** skill; never scan full checkouts) and fold the violations into your triage. Treat the structured rules (swallowed errors, placeholder comments, generic casts, pass-through wrappers, duplicate signatures) as hard finds; don't negotiate with them. If `slop-scan` isn't on PATH, note it and continue — but prefer to install it rather than skip (`npm install -g slop-scan`).

### Scope creep

- Edits unrelated to the stated goal. Split into a separate PR, revert, or retain only with explicit justification in the PR body.
- Auto-formatter noise in files you did not intend to touch. Revert those hunks.
- "Since I was here anyway" refactors that outgrew the ticket. Roll them back and log a follow-up.

## 4. Triage

Group findings by severity. Keep the list short — longer lists signal you are reviewing style, not substance.

- **Must fix** — real bugs, measurable performance cliffs, dead code that would mislead a reviewer, legacy branches that violate `single-canon`.
- **Should fix** — junk code, drift, minor scope creep. Default is to clean.
- **Consider** — stylistic or subjective calls. Flag to the user; do not silently rewrite.

Each finding: `<path>:<line-range>` + one-line reason. No essays.

**Wait for user approval** before editing. Respect drops and downgrades.

## 5. Apply

- <= 5 edits and the prior work is still uncommitted → fold into the pending commit.
- More edits than that, or prior work is already committed → separate commit: `refactor(<scope>): retrospective cleanup`.
- Re-run the project's formatter, linter, and typechecker on changed files. Do not push until clean.

**Hard rule**: do not escalate into an unrelated refactor. If the cleanup starts sprouting new abstractions, touching files outside the original diff, or invalidating its own triage, stop and log the idea as a follow-up ticket. The retrospective is a scalpel, not an excavator.

## 6. Second pass (stop when empty)

If the first pass produced substantive changes, re-read the resulting diff with the same detachment — removing one layer often exposes the next. Stop when a pass yields nothing.
