---
description: Review a PR -- root-cause + typed verification, shared criteria, findings for approval; /post-review publishes.
argument-hint: <PR-number-or-URL>
---

Load skills: **pr-context**, **linear-cli**, **worktree-setup**, **quality-ship**, **voice**, **repo-conventions**.

Treat **voice** as a required review gate, not optional polish: load it before drafting findings so severity, phrasing, and the unprompted-opinion sweep come from the canonical skill.

**Targeted scope = the PR's changed files** (`gh pr diff <PR> --name-only`, or via **pr-context**). Reviewer's job is judgment (architecture, root cause, broader impact, convention adherence, slop), not redundantly re-running green CI — but red and inconclusive checks are yours to triage to root cause (§3). When a step below needs setup or a validator (repro in §3, slop-scan in §4), use **worktree-setup**'s `repair.py` (never `verify.py` — its full-workspace manifest demands out-of-scope artifacts) and **quality-ship**'s validator patterns; don't wing it — that derails focus.

**Workers in flight.** If a subagent is still making progress (output / tool calls visible), **let it finish**. Don't `TaskStop` over resource-usage or token-budget worries — review quality outranks both. Stop only if genuinely stalled or off-task.

**Worker complexity.** Any `Task` dispatched from this flow — coverage sweeps, slop scans, repro runs, per-area reviewers — **must** pass `complexity: "heavy"`. The default `medium` is too weak for review judgment (root-cause tracing, architecture critique, slop discrimination) and produces shallow findings. Don't omit `complexity` or downgrade to save tokens. If a sweep is genuinely trivial (one-file typo PR), do it inline rather than dispatching.

**Get to the crux — verify, don't trust.** The PR's description, claimed invariants, and green-elsewhere CI are hypotheses, not evidence; §3 is how you turn them into fact. A diff that's clean (passes CI, no slop) but doesn't move the root cause — or that a larger in-flight PR already subsumes — is net-zero churn; say so plainly. Rubber-stamping a tidy symptom-patch is the failure mode to avoid.

## 1. Gather context

Follow **pr-context** to fetch metadata, conversation, diff, and linked Linear ticket; derive `REPO` and `HEAD_SHA` from `$ARGUMENTS`.

## 2. Classify PR type

Infer from title prefix, labels, ticket, and changed files:

| Type | Signals |
|------|---------|
| **Bug fix** | title `fix(...)`, label `bug`, ticket describes broken behavior |
| **Feature** | title `feat(...)`, label `feature`/`enhancement`, ticket describes new capability |
| **Refactor/chore** | title `refactor`/`chore`/`perf`/`docs`, no user-facing behavior change |
| **CI/Infra** | title `ci`/`build`, changes only in `.github/`, `infra/`, config files, scripts |

If ambiguous, default to **Feature**.

## 3. Verification

Two disciplines apply to **every** PR type; then the type-specific checks below.

### Root-cause discipline (every type)

The diff won't tell you whether the fix is at the right layer. Before accepting the approach:

- **Trace source → sink.** Follow the data through the real pipeline (producer → transform → consumer/render), not just the changed lines. Confirm the layer the PR touches is where the invariant it claims actually lives.
- **Verify claimed invariants.** Treat every "this makes X stable / Y safe / Z green" as a hypothesis. Build the adversarial case; if it breaks, **prove it with a throwaway probe** (append a temp test → run → restore via `git checkout`/backup) and quote the concrete before/after. An overstated invariant is a `warning`.
- **Hunt prior/parallel art.** Mine the PR's own "related work"/linked refs first, then search merged + open PRs on the same files or root cause (`gh pr list --search "<area>" --state all`; compare changed-file overlap). If a larger in-flight PR already fixes the cause idiomatically, the patch may be net-zero or on a collision course — make that the headline finding (symptom vs root cause), citing the other PR's mechanism.
- **Name it.** State the actual invariant being violated, the layer it belongs to, and whether this change establishes it or just patches one manifestation.

### Triage every red CI check

Don't trust badge colors — classify each failure from its job log (`gh pr checks <PR>` → `gh run view --job=<id> --log-failed`; strip branch-fetch noise with `rg -v "new branch|->"`):

- **Infra flake** — OOM (`exit 134`/`137`, "JavaScript heap out of memory"), runner timeout, network; often fails several untouched packages identically. Note and discount.
- **Unrelated** — failure in a file/shard the diff doesn't touch (flaky e2e on another feature). Note as unrelated.
- **Real** — caused by the diff, or a required gate the PR hasn't met (missing e2e test, opt-out label). This is a finding.

If CI was **inconclusive** (e.g. typecheck OOM'd before reaching the relevant package), run that one check locally and scoped (`--filter`/single package) for a definitive answer — and separate genuine errors from environment artifacts (missing generated deps in a fresh worktree).

### Bug fix

**Reproduce the real thing first** — catches fixes that mask a symptom instead of curing it. A passing test (especially mock-heavy) is the *author's* proxy, not your repro: reproduce the actual user-facing behavior yourself, even when handed a repro command or a green test.

1. **Faithful repro (default, delegated).** Reproduce the real symptom at the highest fidelity available — drive the actual app via **droid-control** (CLI/TUI/web/Electron) or a real request/integration run (services); base shows the bug, HEAD shows it gone, capture before/after as proof. Don't settle for a unit-level stand-in just because the author did. **Delegate to a heavy worker** (`Task`, `complexity: "heavy"`, on **droid-control**; it owns setup — `repair.py`, build) so you stay on review judgment.
   - **Death-spiral guard:** if the worker comes back inconclusive/flaky, *you* own the call — bound any retry, and if it still won't repro, record "couldn't faithfully repro (why)" as a finding and fall through to code-level root-cause analysis. Never recurse into an unbounded repro grind.
2. **Test-level cross-check.** Run the PR's **own new tests against base source**: keep the test files, revert only the source (`git show <base>:<path> > <path>`), run — they MUST fail, for the bug's stated reason (not an import/compile error). Restore (`git checkout HEAD -- <paths>`), confirm green on HEAD. Validates the regression net; does **not** replace step 1.
3. Root-cause review per the discipline above: actual cause or papering over a symptom? Right layer?

### Feature

1. Check against the ticket's acceptance criteria; flag gaps.
2. Evaluate API/UX design -- consistent with existing patterns? Will it age well?

### Refactor/chore

1. Verify **behavior preservation** -- no functional change unless explicitly stated.
2. Check for incomplete migration: missed renames, stale references, orphaned code.

### CI/Infra

1. Pipeline correctness and idempotency (safe to re-run?).
2. Secret handling, permissions scope, exposed surfaces.
3. Loosen code-style scrutiny on YAML/shell.

## 4. Shared review criteria

Load **voice** here if it is not already active. It owns the judgment criteria, canonical severity taxonomy, and mandatory unprompted-opinion sweep; do not invent local tiers or soften findings to checklist language.

Plus the repo's **own documented conventions** -- hold the author to the same standard we hold ourselves. Follow the **repo-conventions** skill (discover + diff-scope against the PR's changed files, then read the selected docs) and reconcile the diff against them. Here you **flag, not fix**: fold each deviation into findings at `warning` (a clear written rule -- error handling, file organization, test placement, flags -- broken) or `suggestion` (softer guidance). A repo-provided pre-PR checklist is itself review criteria -- check the diff against each item.

Plus the **AI-slop validator** (JS/TS only):

```bash
BASE_REF=$(gh pr view <PR> --json baseRefName --jq '.baseRefName')
git fetch origin "$BASE_REF"
BASE_SHA=$(git merge-base "origin/$BASE_REF" "$HEAD_SHA")
BASE_WT=$(mktemp -d); HEAD_WT=$(mktemp -d)
git worktree add --detach "$BASE_WT" "$BASE_SHA"
git worktree add --detach "$HEAD_WT" "$HEAD_SHA"
slop-scan delta "$BASE_WT" "$HEAD_WT" --json
git worktree remove --force "$BASE_WT" && git worktree remove --force "$HEAD_WT"
```

Detached source snapshots — slop-scan reads source, not built artifacts. **Don't repair/verify.** Install if missing: `npm install -g slop-scan`; otherwise skip.

Hits (swallowed errors, placeholder comments, generic casts, pass-through wrappers, duplicate signatures, …) fold into findings at `warning` (likely to fire / hides real failure) or `opinion` (structural smell).

## 5. User approval gate

Show every finding to the user before posting:

- Group by file; include severity, line, suggested fix.
- State intended verdict (`APPROVE` / `COMMENT`) and draft the verdict body (below).
- Plain chat prose; **do not use `AskUser`** -- the user should be free to discuss, reword, drop, or re-severity findings.
- **Wait for explicit confirmation.** Apply any user edits before handoff.

### Draft the verdict body

The verdict is the reviewer's standalone ruling; line comments are the evidence. Recapping "posted N comments on X, Y, Z" is the failure mode to kill -- GitHub renders the threads, restating them adds zero.

Cover, roughly in order:

1. **Disposition and why** -- one sentence: right change at the right layer, or symptom-patch / net-zero / collision with parallel art? Cite the §3 root cause, not the comment count.
2. **Blockers** (`COMMENT` only) -- the one or two findings that actually gate. If it's all `opinion`/`nit`, justify `COMMENT` over `APPROVE` -- or flip.
3. **What you verified** -- the §3 probes (repro, test-against-base, CI triage, slop-scan delta), one line each. Separates review from rubber-stamp.
4. **Headline opinion** -- the unprompted call from **voice** (architecture, scope drift, missing invariant) that doesn't map to a line. Skip if none; don't pad.

Short paragraph or 4-6 bullets; a verdict longer than the diff is its own smell.

Once confirmed, hand off to `/post-review <PR-number-or-URL>` with findings and verdict body. Suggestion-block decisions live there -- review judgment must not be biased toward apply-clickable issues.

## Environment / tooling gotchas

- **Search:** use `rg` (the `Grep` tool and shell `grep`/`git grep` are policy-blocked here). `rg -n` for line numbers — note `-N` *disables* them, so never pass `-nN`.
- **Tests:** run the workspace binary directly (`./node_modules/.bin/vitest …`); `npx vitest` may pull a different major version that fails to load the repo config. Single-file runs can trip a global coverage threshold — add `--coverage.enabled=false`.
- **Worktree:** no `node_modules`? Run `repair.py` (never `npm install` in a worktree). It does **not** run package `generate`/`prepare-*` bun scripts, so generated-dep imports (`@/generated/*`, prepared test harnesses like `@factory/tui-test`) may surface as type errors — those are environment artifacts, not PR defects.
- **Base-repro side effects:** reverting files for step 1 touches mtimes → "file modified externally" reminders are expected; re-read before editing.
