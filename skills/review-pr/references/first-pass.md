# First-pass review

The comprehensive main review. One reviewer (you) owns judgment end to end; workers gather evidence per `worker-contracts.md`. Ends with the **review-state summary** — the approval artifact, the `deeper` input, and the dossier seed.

**Targeted scope = the PR's changed files** (`gh pr diff <PR> --name-only`, or via **pr-context**). Your job is judgment (architecture, root cause, broader impact, convention adherence, slop), not redundantly re-running green CI — but red and inconclusive checks are yours to triage to root cause (§3).

## 1. Gather context

Follow **pr-context** to fetch metadata, conversation, diff, and linked Linear ticket; derive `REPO` and `HEAD_SHA` from the target. Record `HEAD_SHA` — it anchors the dossier.

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

Two disciplines apply to **every** PR type; then the type-specific checks.

### Root-cause discipline (every type)

The diff won't tell you whether the fix is at the right layer. Before accepting the approach:

- **Trace source → sink.** Follow the data through the real pipeline (producer → transform → consumer/render), not just the changed lines. Confirm the layer the PR touches is where the invariant it claims actually lives.
- **Verify claimed invariants.** Treat every "this makes X stable / Y safe / Z green" as a hypothesis. Build the adversarial case; if it breaks, **prove it with a throwaway probe** (append a temp test → run → restore via `git checkout`/backup) and quote the concrete before/after. An overstated invariant is a `warning`.
- **Hunt prior/parallel art.** Mine the PR's own "related work"/linked refs first, then search merged + open PRs on the same files or root cause (`gh pr list --search "<area>" --state all`; compare changed-file overlap). If a larger in-flight PR already fixes the cause idiomatically, the patch may be net-zero or on a collision course — make that the headline finding (symptom vs root cause), citing the other PR's mechanism.
- **Name it.** State the actual invariant being violated, the layer it belongs to, and whether this change establishes it or just patches one manifestation.
- **Record suspicions you cannot settle inline.** An adversarial case you can settle with one bounded probe or trace, settle now — that is this section's job. What remains genuinely open after that goes into the review-state summary's *unresolved suspicions* (exact hypothesis, path, evidence so far, what would settle it) — the raw material for `deeper`. Do not silently drop them, and do not spawn ad-hoc worker waves mid-pass to chase them (that's overcoverage's job, done with pairing and reconciliation).

### Triage every red CI check

Don't trust badge colors — classify each failure from its job log (`gh pr checks <PR>` → `gh run view --job=<id> --log-failed`; strip branch-fetch noise with `rg -v "new branch|->"`):

- **Infra flake** — OOM (`exit 134`/`137`, "JavaScript heap out of memory"), runner timeout, network; often fails several untouched packages identically. Note and discount.
- **Unrelated** — failure in a file/shard the diff doesn't touch (flaky e2e on another feature). Note as unrelated.
- **Real** — caused by the diff, or a required gate the PR hasn't met (missing e2e test, opt-out label). This is a finding. When your own verification proves the gate applies — you reproduced through the very harness it demands — an opt-out label is a cop-out, not an alternative: require the coverage and name the exact test to add; the label deserves dismissal, not rebuttal.

If CI was **inconclusive** (e.g. typecheck OOM'd before reaching the relevant package), run that one check locally and scoped (`--filter`/single package) for a definitive answer — and separate genuine errors from environment artifacts (missing generated deps in a fresh worktree).

### Bug fix

**Reproduce the real thing first** — catches fixes that mask a symptom instead of curing it. A passing test (especially mock-heavy) is the *author's* proxy, not your repro: reproduce the actual user-facing behavior yourself, even when handed a repro command or a green test.

1. **Faithful repro (default, delegated).** Reproduce the real symptom at the highest fidelity available — drive the actual app via **droid-control** (CLI/TUI/web/Electron) or a real request/integration run (services); base shows the bug, HEAD shows it gone, capture before/after as proof. Don't settle for a unit-level stand-in just because the author did. **Delegate to a heavy worker** (per `worker-contracts.md`; it owns setup — `repair.py`, build) so you stay on review judgment.
   - **Death-spiral guard:** if the worker comes back inconclusive/flaky, *you* own the call — bound any retry, and if it still won't repro, record "couldn't faithfully repro (why)" as a finding and fall through to code-level root-cause analysis. Never recurse into an unbounded repro grind.
2. **Test-level cross-check.** Run the PR's **own new tests against base source**: keep the test files, revert only the source (`git show <base>:<path> > <path>`), run — they MUST fail, for the bug's stated reason (not an import/compile error). Restore (`git checkout HEAD -- <paths>`), confirm green on HEAD. Validates the regression net; does **not** replace step 1.
3. Root-cause review per the discipline above: actual cause or papering over a symptom? Right layer?

### Feature

1. Check against the ticket's acceptance criteria; flag gaps.
2. Evaluate API/UX design — consistent with existing patterns? Will it age well?

### Refactor/chore

1. Verify **behavior preservation** — no functional change unless explicitly stated.
2. Check for incomplete migration: missed renames, stale references, orphaned code.

### CI/Infra

1. Pipeline correctness and idempotency (safe to re-run?).
2. Secret handling, permissions scope, exposed surfaces.
3. Loosen code-style scrutiny on YAML/shell.

## 4. Shared review criteria

Load **voice** here if not already active. It owns the judgment criteria, canonical severity taxonomy, and mandatory unprompted-opinion sweep; do not invent local tiers or soften findings to checklist language.

Plus the repo's **own documented conventions** — hold the author to the same standard we hold ourselves. Follow **repo-conventions** (discover + diff-scope against the PR's changed files, then read the selected docs) and reconcile the diff against them. **Flag, not fix**: fold each deviation into findings at `warning` (a clear written rule — error handling, file organization, test placement, flags — broken) or `suggestion` (softer guidance). A repo-provided pre-PR checklist is itself review criteria — check the diff against each item.

Plus the **structural sweep** (every PR): dispatch a heavy worker with the **structural-review** skill as its objective — the behavior-preserving reframing hunt that correctness review misses. Findings return in **voice** tiers; fold them in, dedupe against slop-scan hits on the same lines, and hold the flag-not-fix line. A one-file typo PR still gets the sweep, inline instead of dispatched.

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

## 5. Review-state summary

Produce this before the approval gate — it is the bridge to `deeper`, the dossier seed, and the honest record of what you did and didn't settle:

```text
REVIEW STATE — PR <number> @ <HEAD_SHA>

Confirmed findings:
- <severity> <file:line> — <claim> — <evidence>

Unresolved suspicions:
- <precise hypothesis>
  path: <producer → transform → consumer>
  evidence so far: <what you established>
  would settle it: <exact trace or probe>
  impact if real: <user-visible consequence>

Verified-safe:
- <suspicion killed> — <the invariant/probe that killed it>

Coverage map:
- <surface>: covered by <main/worker/probe> — <outcome>
- <surface>: not deeply covered — risk <low/medium/high>

Candidate overcoverage categories (only if warranted):
- <category> — <why a second evidence modality would add information>
```

If unresolved suspicions or high-risk uncovered surfaces remain, recommend `deeper` — but do not launch it without the user's go-ahead. The summary travels with the approval-gate presentation (§6), so the user rules on findings and the `deeper` recommendation together.

## 6. User approval gate

Show every finding to the user before posting:

- Group by file; include severity, line, suggested fix.
- State intended verdict (`APPROVE` / `COMMENT`) and draft the verdict body (below).
- Plain chat prose; **do not use `AskUser`** — the user should be free to discuss, reword, drop, or re-severity findings.
- **Wait for explicit confirmation.** Apply any user edits before handoff.

### Draft the verdict body

The verdict is the reviewer's standalone ruling; line comments are the evidence. Recapping "posted N comments on X, Y, Z" is the failure mode to kill — GitHub renders the threads, restating them adds zero. The audience is the PR author: the approval-gate discussion (draft revisions, severity re-calibrations, dropped findings) is invisible to them and never referenced in the body.

Cover, roughly in order:

1. **Disposition and why** — one prose sentence: right change at the right layer, or symptom-patch / net-zero / collision with parallel art? Cite the §3 root cause, not the comment count. Never open with the literal event token ("COMMENT." / "APPROVE."); GitHub already badges the review state, so the body starts with the *why*.
2. **Blockers** (`COMMENT` only) — the one or two findings that actually gate, each a numbered imperative ask naming the concrete mechanism: the exact test/fixture/flag to add, the invariant it must assert, the call site to move. Standard-protocol asks (test coverage, ticket reference, meeting a CI gate) are requirements, not requests — state them flatly. Never argue for them, pre-empt pushback, or plead the gate's legitimacy — real-vs-flake triage is evidence per point 3, stated once as fact, never a case for compliance. Detail that needs a paragraph belongs in the line comment; the verdict names the requirement. If it's all `opinion`/`nit`, justify `COMMENT` over `APPROVE` — or flip.
3. **Evidence, woven in** — attach the probe to the claim it backs (*"the new tests fail on base for the stated reason"*), inline, as the observed fact. **Never the commands behind it**: CLI invocations, tool names, "Checks run:" paragraphs, CI counts, and sweep inventories are process narration that buries the findings. A probe that supports no specific claim doesn't appear.
4. **Headline opinion** — the unprompted call from **voice** (architecture, scope drift, missing invariant) that doesn't map to a line. Skip if none; don't pad.

Pre-existing issues discovered en route ("worth a ticket", fast-follows) go to a ticket or a PR conversation comment, not a verdict paragraph.

Shape: one ruling sentence, the numbered blockers, a short non-gating paragraph. A verdict longer than the diff is its own smell.

Once confirmed: hand off to `/post-review <PR>` with findings and verdict body (suggestion-block decisions live there — review judgment must not be biased toward apply-clickable issues), and **write the dossier** per `dossier.md`.
