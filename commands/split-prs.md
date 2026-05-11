---
description: Break a branch's commits into clean, separate PRs (atomic or stacked)
argument-hint: <branch-name> [--base <base-branch>]
---

Load skills: **split-pr** (primary -- drives the whole flow), **ticket-branch**, **quality-ship**, **pr-description**, **git-advanced**, **pr-context**.

Follow the **split-pr** skill end-to-end:

1. **Analyze the diff** (skill section 1) -- build the concern map, classify commits, pull the flat file list.
2. **Propose the plan** (skill section 2) -- write the full plan per the skill's format, apply the standalone-review test, and **wait for user approval** before touching any branch.
3. **Pick the shape** (skill section 3) -- atomic by default; stacked only when the decision table forces it. Follow `references/atomic.md` or `references/stacked.md` for the chosen path.
4. **Execute** (skill section 4) -- pre-split commit surgery if needed (4a), then the per-PR loop (4b) with quality-ship + pr-description hand-offs, handling cherry-pick conflicts per 4c.
5. **Report** (skill section 5) -- URLs, shape, dependency graph, merge order.

Re-read the relevant `references/*.md` when executing; do not work from memory on branch mechanics, restacking, or merge-strategy implications.
