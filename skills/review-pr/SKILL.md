---
name: review-pr
description: "Load only when the user invokes /review-pr or explicitly asks for a PR review, deeper pass, or re-review; never ambiently."
user-invocable: true
---

# Review PR

Router + shared policy only. Mode playbooks live in `references/workflows/`, judgment lenses in `references/lenses/`, and shared machinery (dossier, workers) in `references/systems/`; load exactly the workflow you route to, and each lens or system when a workflow calls for it. Do not reabsorb mode content into this file.

Load order for a first pass: `references/workflows/first-pass.md` → at its §3, `references/lenses/architecture.md` (the gate's single owner) → on `continue`, the rest of first-pass, including the standing structural sweep (`references/workflows/first-pass.md` §4) and `references/lenses/acceptance.md` (sole owner of hands-on acceptance). Each standing worker's loads, scope, and return are fixed by the file that dispatches it: `references/lenses/architecture.md` §8, `references/workflows/first-pass.md` §4, `references/lenses/acceptance.md`.

## Invocation

Input: `/review-pr <target> [mode] [operator context...]`

- **Target**: first token that resolves to a PR — number, `#number`, or GitHub PR URL. If absent, infer from the worktree dossier (`./.agents/review.md`) or the current branch's open PR; if both fail, ask. Bare-keyword invocations ("deeper", "re-review") are valid — mode from the keyword, target inferred.
- **Mode keyword** (optional, anywhere in the trailing text):
  - `deeper` → **overcoverage** (`references/workflows/deeper.md`)
  - `follow-up` / `re-review` → **follow-up** (`references/workflows/follow-up.md`)
  - `ground-up` → **ground-up** (`references/workflows/ground-up.md`)
  - none → auto-detect (below)
- **Modifier** `crux` (optional; combines with first-pass or follow-up, where it forces a gate rerun): the architecture gate builds its shape from first principles with `references/lenses/crux.md` (`references/lenses/architecture.md` §5). `ground-up` always runs that lens.
- **Everything else is operator context** — constraints, focus areas, known history ("author force-pushed", "skip the frontend surface"). Honor it; it overrides auto-detection but never lowers the evidence bar or skips the approval gate.

## Routing

Auto-detect (no mode keyword) — check `./.agents/review.md` (worktree-local dossier; PR number inside must match the target) first:

| Condition | Mode |
|---|---|
| No prior review by us on this PR | **first-pass** → `references/workflows/first-pass.md` |
| Dossier exists, or our prior review is on the GitHub thread — including when only the PR body or its evidence changed since (head SHA unchanged) | **follow-up** → `references/workflows/follow-up.md` |

Rules:

- **Overcoverage (`deeper` → `references/workflows/deeper.md`) after a first pass is never auto-selected** — explicit keyword, or user approval of the first-pass "candidate overcoverage categories" recommendation. Follow-up is the exception: it runs the wave by default over its own residue (`references/workflows/follow-up.md` §5). Fan-out is a deliberate decision, and it is never recommended after a `revise` gate ruling (`references/workflows/deeper.md` precondition). Its input is the review-state summary: same-session first pass, or seeded from the dossier's unresolved/coverage sections when the head is unchanged (head moved → follow-up first).
- **`ground-up` is never auto-selected** — explicit keyword, or user approval of first-pass's complexity recommendation (`references/workflows/first-pass.md` §1). It runs the first pass and the `deeper` wave inside itself, against a reference design built blind to the PR.
- **follow-up always starts from the dossier** (`references/systems/dossier.md`), never by replaying the original review transcript. If invoked inside a stale mega-session, say so and recommend a fresh session.
- **Mode keywords are requests, not facts.** Missing precondition (`deeper` with no first pass and no dossier; `follow-up` with no prior review anywhere) → say so and run the mode whose precondition holds.

## Shared invariants (all modes)

1. **Verify, don't trust.** The PR's description, claimed invariants, architectural framing ("consolidates", "normalizes", "replaces N paths with one"), and green-elsewhere CI are hypotheses. A diff that's clean but doesn't move the root cause — or that a larger in-flight PR subsumes — is net-zero churn; say so plainly. Rubber-stamping a tidy symptom-patch is the failure mode; its twin is hedging on a requirement your own evidence has already settled — once verification proves a standard applies, enforcing it is not a negotiation. Evidence counts at the boundary it exercised: lower-level probes never stand in for an assigned user-workflow or native-platform claim (`references/lenses/acceptance.md`), and a review with a required scenario open never calls itself complete.
2. **Problem → shape → lines.** The architecture gate (`references/lenses/architecture.md`, called from `references/workflows/first-pass.md` §3 and, on a reshaped delta, `references/workflows/follow-up.md` §2) rules `continue` / `revise` from current source before detailed verification; the main reviewer owns the ruling and admits worker evidence before using it. On `continue`, root-cause tracing goes to line depth: the invariant, its layer, and whether the change establishes it or patches one manifestation.
3. **Flag, not fix.** Review output is findings, never edits to the PR branch.
4. **Voice is the judgment gate.** Load **voice** before drafting any finding; severities, phrasing, and the unprompted-opinion sweep come from it, not local invention.
5. **User approval before posting.** Present findings + draft verdict in plain chat prose (never `AskUser`), wait for explicit confirmation, then hand off to `/post-review`.
6. **Workers follow the contract.** Before the first `Task` dispatch in any mode, load `references/systems/workers.md` — complexity-by-responsibility, output schema, reconciliation, and cancellation rules live there. Every mode obeys it.
7. **Ledger discipline.** Scaffold the paired ledger (`references/systems/dossier.md`: `review.md` current state + append-only `review.notes.md`) at review start, before verification. Notes entries are appended **in the same turn as the event they record** — candidate, confirm/kill, fold, retier, dispatch, reconciliation, gate decision, post — never batched to end-of-phase; a context compaction between turns must never cost a conclusion. Workers never touch either file. Every follow-up starts by loading the dossier and continues the same notes log.
8. **Views compress, never decorate.** Load `show-me` for a verified source→sink trace, state flow, or dependency chain spanning more than two actors, and for the verdict's required view (`references/workflows/first-pass.md` §6 owns what it draws and what is cut). Elsewhere, surface a view only where it replaces a prose chain in the review state or a finding.

## Shared skill loads

All modes load: **pr-context**, **linear-cli**, **voice**, **repo-conventions**, **worktree-setup**, **quality-ship**. First-pass additionally reads `references/lenses/structure.md` (architecture gate and structural sweep) and, through its acceptance worker, **droid-control** plus the surface-fidelity skill a claim triggers; multi-finding reconciliation uses **patch-coherence**. Ground-up's blind workers add research loads (`references/workflows/ground-up.md` §2). The **description audit** (`references/workflows/first-pass.md` §1) loads **pr-description** in read-only audit posture: that skill is the sole owner of what a good PR body requires; review owns only when to check it and how to tie its claims to evidence. Loading it authorizes no drafting, PATCH, capture, or upload.

When a step needs setup or a validator (repro, slop-scan, scoped test runs), use **worktree-setup**'s `repair.py` and **quality-ship**'s validator patterns; don't wing it — improvised invocations derail focus (and an unfiltered turbo run eats ~9 GB RAM).

## Environment / tooling gotchas (all modes)

- **Search:** use `rg` (the `Grep` tool and shell `grep`/`git grep` are policy-blocked here). `rg -n` for line numbers — `-N` *disables* them; never pass `-nN`.
- **Tests:** run through **quality-ship**'s attached runner — `~/.agents/scripts/run-check test --cwd <pkg> -- ./node_modules/.bin/vitest run …` — never `npx vitest`, which may pull a different major. Single-file runs can trip global coverage thresholds — add `--coverage.enabled=false`.
- **Worktree:** no `node_modules`? Run **worktree-setup**'s `repair.py` (never `npm install` in a worktree; never `verify.py` — its full-workspace manifest demands out-of-scope artifacts). `repair.py` does **not** run package `generate`/`prepare-*` bun scripts, so generated-dep imports (`@/generated/*`, prepared harnesses like `@factory/tui-test`) may surface as type errors — environment artifacts, not PR defects.
- **Base/HEAD comparisons:** never revert or restore source in the live checkout — verification-target and snapshot ownership live in `references/systems/workers.md`.
