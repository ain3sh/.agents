---
name: repo-conventions
description: Shared atom for discovering and applying a repo's own documented conventions (error handling, file organization, style, test placement, feature flags) to the change at hand. Background knowledge for workflow commands -- not invoked directly.
user-invocable: false
---

# Repo Conventions

A repo's docs **are** its review standards. Validators (lint, types, tests) enforce mechanics but are blind to the idioms a repo writes down in prose -- error handling, file/module organization, language style, test placement, flag usage -- which is exactly what reviewers flag once the gate is green. Close the gap the way quality-ship's tooling table does: **detection-driven, no filenames hardcoded.**

Two entry points, one machine:

- **Early** (implementation/exploration): steps 1-2, to surface the conventions governing the *area of change* before writing code -- so the spec and diff conform from the start, not retrofitted at the gate.
- **Gate** (pre-commit): steps 1-4, to reconcile the *final diff*, fix violations, and emit the checklist row.

## 1. Discover (cheap)

Glob the well-known convention homes; read only each hit's **title + frontmatter + intro** (`Read` with `limit: 15`) -- enough to know what it governs, not the body. Build the manifest fresh in context each run; never persist a cache.

| Location | Usually holds |
|----------|---------------|
| `docs/**`, `doc/**`, `documentation/**` | conventions, guides, pre-PR checklists |
| `CONTRIBUTING*`, `.github/CONTRIBUTING.md` | contribution rules, pre-PR steps |
| `AGENTS.md`, `CLAUDE.md`, `.cursor/rules/**`, `.cursorrules` | agent-targeted coding rules |
| root `*.md` like `STYLE`, `CONVENTIONS`, `ARCHITECTURE` | style / architecture norms |

Manifest per doc: `{ path, title, summary, applies-to }`. Take `applies-to` from the doc's frontmatter/prose when stated (e.g. "applies to `*.tsx`"); otherwise infer from the title. No hits = `no signal`, like a missing config -- don't invent rules.

## 2. Select (diff-scoped)

Get the change's shape -- **gate:** `git diff --name-only HEAD` + `--cached`; **early:** the files/dirs the ticket will touch -- then scan for cues: extensions, new vs. modified files, `try`/`catch`, `use*` hooks, flag calls, test files, migrations. Keep only manifest entries whose scope intersects:

- `applies-to` (or title) matches a changed path / extension / cue → **in**.
- A repo-provided **pre-PR checklist** → **always in**; it is the repo stating its own gate.
- Unsure → **include**. A misread doc costs tokens; a skipped one costs a review round.
- Budget `<= 6`; if more match, keep the most directly overlapping.

## 3. Apply

Read the **selected** docs in full, extract their concrete rules, and make the change conform -- fix the code, never annotate around a rule. The doc is the spec; the diff must match it.

- **Axes don't overlap:** tools own mechanics (format/lint/types); docs own what tools can't check -- error idioms, organization, naming, test placement, flag usage.
- **Stale doc:** if one contradicts lived repo reality (surrounding code consistently does otherwise), flag it as a *consider* rather than silently follow -- the user makes the call.

## 4. Record (gate only)

One row, folded into quality-ship's gate checklist:

```
conventions:
  discovered: <n @ docs/, CONTRIBUTING.md>      [evidence: glob]
  applied:    <doc-a, doc-b>   (reason: <diff touches ...>)
  skipped:    <doc-c (no flag touched), doc-d (no new files)>
  result:     <pass | violations: path:line -- rule>
```

`no signal` only when discovery truly found nothing -- never because reading was inconvenient.
