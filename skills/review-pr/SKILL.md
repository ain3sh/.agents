---
name: review-pr
description: Full PR review workflows -- first-pass, deeper (overcoverage), follow-up (re-review). Load when the user invokes /review-pr or explicitly asks for a PR review, deeper wave, or re-review; never ambiently.
user-invocable: true
---

# Review PR

Router + shared policy only. The mode playbooks live in `references/`; load exactly the one you route to. Do not reabsorb mode content into this file.

## Invocation

Input: `/review-pr <target> [mode] [operator context...]`

- **Target**: first token that resolves to a PR — number, `#number`, or GitHub PR URL. If absent, infer from the worktree dossier (`./.agents/review.md`) or the current branch's open PR; if both fail, ask. Bare-keyword invocations ("deeper", "re-review") are valid — mode from the keyword, target inferred.
- **Mode keyword** (optional, anywhere in the trailing text):
  - `deeper` → **overcoverage** (`references/overcoverage.md`)
  - `follow-up` / `re-review` → **follow-up** (`references/follow-up.md`)
  - none → auto-detect (below)
- **Everything else is operator context** — constraints, focus areas, known history ("author force-pushed", "skip the frontend surface"). Honor it; it overrides auto-detection but never lowers the evidence bar or skips the approval gate.

## Routing

Auto-detect (no mode keyword) — check `./.agents/review.md` (worktree-local dossier; PR number inside must match the target) first:

| Condition | Mode |
|---|---|
| No prior review by us on this PR | **first-pass** → `references/first-pass.md` |
| Dossier exists, or our prior review is on the GitHub thread | **follow-up** → `references/follow-up.md` |

Rules:

- **Overcoverage (`deeper` → `references/overcoverage.md`) is never auto-selected** — explicit keyword, or user approval of the first-pass "candidate overcoverage categories" recommendation. Fan-out is a deliberate decision. Its input is the review-state summary: same-session first pass, or seeded from the dossier's unresolved/coverage sections when the head is unchanged (head moved → follow-up first).
- **follow-up always starts from the dossier** (`references/dossier.md`), never by replaying the original review transcript. If invoked inside a stale mega-session, say so and recommend a fresh session.
- **Mode keywords are requests, not facts.** Missing precondition (`deeper` with no first pass and no dossier; `follow-up` with no prior review anywhere) → say so and run the mode whose precondition holds.

## Shared invariants (all modes)

1. **Verify, don't trust.** The PR's description, claimed invariants, and green-elsewhere CI are hypotheses. A diff that's clean but doesn't move the root cause — or that a larger in-flight PR subsumes — is net-zero churn; say so plainly. Rubber-stamping a tidy symptom-patch is the failure mode; its twin is hedging on a requirement your own evidence has already settled — once verification proves a standard applies, enforcing it is not a negotiation.
2. **Root-cause first.** Trace source → sink through the real pipeline; name the invariant, the layer it lives in, and whether the change establishes it or patches one manifestation.
3. **Flag, not fix.** Review output is findings, never edits to the PR branch.
4. **Voice is the judgment gate.** Load **voice** before drafting any finding; severities, phrasing, and the unprompted-opinion sweep come from it, not local invention.
5. **User approval before posting.** Present findings + draft verdict in plain chat prose (never `AskUser`), wait for explicit confirmation, then hand off to `/post-review`.
6. **Workers follow the contract.** Before the first `Task` dispatch in any mode, load `references/worker-contracts.md` — complexity-by-responsibility, output schema, reconciliation, and cancellation rules live there. Every mode obeys it.
7. **Dossier discipline.** Every posted review writes/updates the dossier (`references/dossier.md`); every follow-up starts by loading it.

## Shared skill loads

All modes load: **pr-context**, **linear-cli**, **voice**, **repo-conventions**, **worktree-setup**, **quality-ship**. First-pass additionally uses **structural-review**; repro paths use **droid-control**; multi-finding reconciliation uses **patch-coherence**.

When a step needs setup or a validator (repro, slop-scan, scoped test runs), use **worktree-setup**'s `repair.py` and **quality-ship**'s validator patterns; don't wing it — improvised invocations derail focus (and an unfiltered turbo run eats ~9 GB RAM).

## Environment / tooling gotchas (all modes)

- **Search:** use `rg` (the `Grep` tool and shell `grep`/`git grep` are policy-blocked here). `rg -n` for line numbers — `-N` *disables* them; never pass `-nN`.
- **Tests:** run the workspace binary directly (`./node_modules/.bin/vitest …`); `npx vitest` may pull a different major. Single-file runs can trip global coverage thresholds — add `--coverage.enabled=false`.
- **Worktree:** no `node_modules`? Run **worktree-setup**'s `repair.py` (never `npm install` in a worktree; never `verify.py` — its full-workspace manifest demands out-of-scope artifacts). `repair.py` does **not** run package `generate`/`prepare-*` bun scripts, so generated-dep imports (`@/generated/*`, prepared harnesses like `@factory/tui-test`) may surface as type errors — environment artifacts, not PR defects.
- **Base-repro side effects:** reverting files touches mtimes → "file modified externally" reminders are expected; re-read before editing.
