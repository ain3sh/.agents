# First-pass review

The comprehensive main review. One reviewer (you) owns judgment end to end; workers gather evidence per `worker-contracts.md`. Ends with the **review-state summary** — the approval artifact, the `deeper` input, and the dossier seed.

**Targeted scope = the PR's changed files** (`gh pr diff <PR> --name-only`, or via **pr-context**). Your job is judgment (architecture, root cause, broader impact, convention adherence, slop), not redundantly re-running green CI — but red and inconclusive checks are yours to triage to root cause (§3).

## 1. Gather context

Follow **pr-context** to fetch metadata, conversation, diff, and linked Linear ticket; derive `REPO` and `HEAD_SHA` from the target. Record `HEAD_SHA` — it anchors the dossier — and **scaffold the ledger pair now** (`dossier.md`: `review.md` + `review.notes.md`), before verification begins. From here on, every candidate finding, kill, fold, tier change, dispatch, and reconciliation gets a notes entry in the same turn it happens. Record `body_seen` (raw-body fingerprint plus last-edit timestamp, per `dossier.md`) in the dossier header — follow-up uses it to detect body-only changes.

### Description audit (readiness)

Hold the author to the standard we hold ourselves: load **pr-description** — its `SKILL.md` and the references it names for required sections, conditional triggers, visual proof, and refresh staleness — in **read-only audit posture**. It is the sole owner of *what* a body must contain and *when* a section applies (its exemptions bind us too: a section whose trigger does not fire is not missing). This file owns only *when* to check and *how* to tie claims to evidence. Loading it authorizes no drafting, PATCH, capture, or upload; flag-not-fix covers the body.

Walk its criteria against this PR's diff and record two lists as `candidate` notes entries: **claims** the body makes that evidence can settle (behavior anchored to a commit, repro steps, visual artifact, risk mitigation, contract or architecture statement) with what would settle each, and **required material** the criteria demand for this diff that is absent or substituted (pr-description also defines the substitutions that do not count). Record for each cited artifact its identity and access state (URL or attachment, viewable or not, the commit it anchors to) — one line each, not a verification database. No expensive proof work (repro, artifact comparison, probes) before the architecture gate; a claim your source reading settles while tracing is settled then and recorded (`confirm`/`kill`). A description gap is a finding, never by itself an architecture `revise`.

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

Two phases. The **architecture gate** runs first on every PR type and rules `continue` or `revise`. Every later subsection of §3, and all of §4, runs only on `continue` — and runs in full; the gate waives nothing downstream, and a `revise` implies nothing downstream is safe.

### Architecture gate (every type)

Load `architecture-gate.md` — the gate's single owner — and run it before any detailed work. From your §1 intake and initial current-source read, select the **primary changed boundary or authoritative locus** — the shared caller/owner for a routing change; otherwise the changed implementation, contract, state model, config, or document — with its current owner(s) and actual consumers or readers, then dispatch the standing **architecture worker** (subagent type and fallback rule fixed in that file's last section; `worker-contracts.md` admits it as a standing dispatch), handing it the **current-source slice** that section defines — source facts and constraints only, no expected finding. It reads the gate guide and **structural-review** only, returns a gate report with a proposed ruling, and stops; it never receives this file or the detailed flow below. The slice bounds the worker, not you: the rest of the PR and the whole-change judgment stay yours, and a bounded report never marks untouched surfaces verified. A genuinely trivial PR (one-file typo) runs the gate inline instead of dispatching; every other PR dispatches.

Admit the worker's report first (`architecture-gate.md` "Admission"): incomplete or self-contradictory route evidence is incomplete coverage — request the missing trace; never continue from it. Rule only after reconciling an admitted report against your own trace (`reconcile` notes entry) — liking the shape early is not evidence, and detail work started under an unreconciled report is the failure this gate exists to prevent. A `revise` already decisive from your own source evidence may be ruled without waiting; the running worker then falls under the cancellation rules in `worker-contracts.md` (proposition settled or scope withdrawn — record why; never a budget stop), and anything it returned is folded in. The ruling is yours in every case.

Record it as a `gate` notes entry — decision, reason quoting the deciding loci (or the verified absence/necessity), and on `revise` the areas left unreviewed — and mirror it in the dossier's *Architecture gate* section.

- **`continue`** → the rest of this section and §4, in full.
- **`revise`** → skip the rest of §3 and §4; go to §5 with the ruling, then §6 with a standalone `COMMENT` verdict. Severe defects already observed while tracing stay in the findings — a structural stop hides nothing, and nothing is hunted to justify it. Description-audit claims already settled while tracing keep their outcome; the remaining ones are reported as *not checked*, and required-material gaps established at readiness stay as findings. `deeper` never runs on a rejected shape unless the user explicitly asks for it.

### Root-cause discipline

The diff won't tell you whether the fix is at the right layer. Now go to line depth:

- **Trace source → sink in full.** Follow the data through the real pipeline (producer → transform → consumer), every changed line included. Confirm the layer the PR touches is where the invariant it claims actually lives.
- **Verify claimed invariants.** Treat every "this makes X stable / Y safe / Z green" as a hypothesis. Build the adversarial case; if it breaks, **prove it with a throwaway probe** on a parent-arranged disposable snapshot (mechanics in `worker-contracts.md` — never temp-test-then-`git checkout` in the live checkout) and quote the concrete before/after. An overstated invariant is a `warning`.
- **Name it.** State the actual invariant being violated, the layer it belongs to, whether this change establishes it or just patches one manifestation, and — from the gate report's rows — whether every common behavior ends the change with exactly one owner.
- **Record suspicions you cannot settle inline.** An adversarial case you can settle with one bounded probe or trace, settle now — that is this section's job. What remains genuinely open after that goes to the notes as a `candidate` entry (assign its `F<id>`; exact hypothesis, path, evidence so far, what would settle it) and surfaces in the review-state summary's *unresolved suspicions* — the raw material for `deeper`. Do not silently drop them, and do not spawn ad-hoc worker waves mid-pass to chase them (that's overcoverage's job, done with pairing and reconciliation).

### Triage every red CI check

Don't trust badge colors — classify each failure from its job log (`gh pr checks <PR>` → `gh run view --job=<id> --log-failed`; strip branch-fetch noise with `rg -v "new branch|->"`):

- **Infra flake** — OOM (`exit 134`/`137`, "JavaScript heap out of memory"), runner timeout, network; often fails several untouched packages identically. Note and discount.
- **Unrelated** — failure in a file/shard the diff doesn't touch (flaky e2e on another feature). Note as unrelated.
- **Real** — caused by the diff, or a required gate the PR hasn't met (missing e2e test, opt-out label). This is a finding. When your own verification proves the gate applies — you reproduced through the very harness it demands — an opt-out label is a cop-out, not an alternative: require the coverage and name the exact test to add; the label deserves dismissal, not rebuttal.

If CI was **inconclusive** (e.g. typecheck OOM'd before reaching the relevant package), run that one check locally and scoped (`--filter`/single package) for a definitive answer — and separate genuine errors from environment artifacts (missing generated deps in a fresh worktree).

### Hands-on acceptance (every type, on `continue`)

Load `acceptance.md` — its sole owner — and select the scenarios this change requires from affected behavior, lifecycle transitions, and platform support, not from the type row above. Define each scenario's target, entry, state, actions, expected observation, and settled claim before dispatching the standing **acceptance worker** (subagent type, assignment, return, and admission fixed there; `worker-contracts.md` admits it as a standing dispatch) against a stable isolated target you arranged. Admit its return per `acceptance.md` — inspect the evidence contents, then judge the boundary actually exercised against the boundary assigned — and carry every scenario's state into §5 and §6. Root-cause probes below settle mechanisms; they never close an acceptance scenario.

### Bug fix

**Reproduce the real thing** — catches fixes that mask a symptom instead of curing it. Where acceptance selection (`acceptance.md`) finds a real entry, the bug fix's scenario is the faithful comparison: base shows the symptom, head shows it gone, at that entry; a fix with no such surface is `n/a` there with its source reason, and no workflow is invented for it. A scenario left open after acceptance's one bounded re-dispatch is recorded in its own state — never an unbounded repro grind — and review falls through to code-level root-cause analysis.

1. **Test-level cross-check.** Run the PR's **own new tests against base source** on parent-arranged disposable snapshots (mechanics owned by `worker-contracts.md` — never revert or restore source inside the live checkout): they MUST fail on base for the bug's stated reason (not an import/compile error) and pass on HEAD. Validates the regression net; does **not** replace the acceptance scenario — a source-only trace is not a faithful runtime repro.
2. Root-cause review per the discipline above: actual cause or papering over a symptom? Right layer?

### Description claims (every type, on `continue`)

Reconcile the §1 claims list inside the verification you are already doing — same target, hygiene, and fidelity rules; no second worker or capture role. A body repro or walkthrough recipe is input to the acceptance scenario for its surface, whatever the PR type (a recipe pr-description disqualifies is a gap, not a repro). A visual artifact is viewed and compared with head behavior observed in the acceptance scenario that exercises that surface — the same run, not a second capture. Commit-anchored claims are checked against the branch and the paths changed since the anchor, per pr-description's refresh staleness rules. Each claim ends **verified**, **false** (contradicted by your evidence), **stale** (anchor predates changes to the cited path), or **unverifiable** (artifact not viewable, environment unavailable) — unverifiable is reported as exactly that, never as false. Severity is **voice**'s call from materiality, not from the evidence state: stale or inaccessible material that is the *sole* support for a merge-defining claim can block confidence without alleging falsity, while the same state on a peripheral claim is a light ask. Name in each finding the exact re-verification or replacement evidence asked of the author.

### Feature

1. Check against the ticket's acceptance criteria; flag gaps.
2. Evaluate API/UX design — consistent with existing patterns? Will it age well?

### Refactor/chore

1. Verify **behavior preservation** — no functional change unless explicitly stated.
2. Check for incomplete migration: missed renames, stale references, orphaned code.
3. A consolidation claim was settled at the architecture gate, not by the line count; do not relitigate it from the diff stat.

### CI/Infra

1. Pipeline correctness and idempotency (safe to re-run?).
2. Secret handling, permissions scope, exposed surfaces.
3. Loosen code-style scrutiny on YAML/shell.

## 4. Shared review criteria

Runs on `continue` only (§3). Load **voice** here if not already active. It owns the judgment criteria, canonical severity taxonomy, and mandatory unprompted-opinion sweep; do not invent local tiers or soften findings to checklist language.

Plus the repo's **own documented conventions** — hold the author to the same standard we hold ourselves. Follow **repo-conventions** (discover + diff-scope against the PR's changed files, then read the selected docs) and reconcile the diff against them. **Flag, not fix**: fold each deviation into findings at `warning` (a clear written rule — error handling, file organization, test placement, flags — broken) or `suggestion` (softer guidance). A repo-provided pre-PR checklist is itself review criteria — check the diff against each item.

Plus the **architecture worker**'s structural findings — already reconciled at the gate (§3); there is no second structural sweep and nothing here waits on a return. Fold them in **voice** tiers, dedupe against slop-scan hits on the same lines, and hold the flag-not-fix line.

Plus the **AI-slop validator** (JS/TS only): build base/HEAD changed-files temp dirs per **quality-ship**'s slop-scan recipe in `validator-recipes.md` — never worktrees or full source scans — then run it attached:

```bash
~/.agents/scripts/run-check ai-slop -- slop-scan delta <base-tmp-dir> <head-tmp-dir> --json --fail-on added,worsened
```

slop-scan reads source, not built artifacts; the temp dirs hold changed files only. **Don't repair/verify.** Install if missing: `npm install -g slop-scan`; otherwise skip.

Hits (swallowed errors, placeholder comments, generic casts, pass-through wrappers, duplicate signatures, …) fold into findings at `warning` (likely to fire / hides real failure) or `opinion` (structural smell).

## 5. Review-state summary

Produce this before the approval gate — it is the bridge to `deeper` and the honest record of what you did and didn't settle. It is generated *from* the ledger, not from memory: findings and kills should already be notes entries by now. Refresh `review.md` to match (first dossier checkpoint).

```text
REVIEW STATE — PR <number> @ <HEAD_SHA>

Architecture gate: <continue | revise> — <one-line reason: the shape stands, or the defect and the direction>
Gate report: <the admitted, reconciled architecture-gate.md "Gate report" — case, dispatch predicate or n/a, remaining range, rows with quoted deciders>
Description audit: <claims settled: verified/false/stale/unverifiable; not checked: <remaining, on revise>; required material missing: list>
Acceptance (acceptance.md):
- <scenario — surface/platform/mode>: <state, acceptance.md §4 vocabulary verbatim; failed → observation + attribution (F<id> once attributed to the PR | pre-existing → out-of-scope route | unsettled); blocked → blocker + next decision; waived → unverified limit; n/a → source reason>; evidence <probe | integration | end-to-end workflow>, <artifact ref, contents inspected>

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
- <surface>: covered by <main/worker/probe/acceptance> at <source inspection | probe | integration | end-to-end workflow> — <outcome>   (source inspection is truthful for static reads; it never closes an acceptance scenario and is never called a probe)
- <surface>: not deeply covered — risk <low/medium/high>

Unreviewed (revise only):
- <area> — not reviewed; stopped at the architecture gate

Candidate overcoverage categories (only if warranted; never after revise):
- <category> — <why a second evidence modality would add information>
```

On `revise`, the coverage map holds only what you actually established while tracing; every other changed surface goes under *Unreviewed*, and *Verified-safe* lists nothing you did not verify.

An open acceptance scenario is not an overcoverage category and no wave substitutes for it. If unresolved suspicions or high-risk uncovered surfaces remain after a `continue`, recommend `deeper` — but do not launch it without the user's go-ahead. The summary travels with the approval-gate presentation (§6), so the user rules on findings and the `deeper` recommendation together.

## 6. User approval gate

Show every finding to the user before posting:

- Group by file; include severity, line, suggested fix.
- State intended verdict (`APPROVE` / `COMMENT`) and draft the verdict body (below). Never propose `REQUEST_CHANGES` unless the user explicitly asks for that verdict type.
- Plain chat prose; **do not use `AskUser`** — the user should be free to discuss, reword, drop, or re-severity findings.
- **Wait for explicit confirmation.** Apply any user edits before handoff, and record them as notes entries (`gate` for drops/rewording/verdict choice, `retier` for severity changes) — the posted body never references this discussion, but the ledger keeps it.

### Draft the verdict body

The verdict is the reviewer's standalone ruling; line comments are the evidence. Recapping "posted N comments on X, Y, Z" is the failure mode to kill — GitHub renders the threads, restating them adds zero. The audience is the PR author: the approval-gate discussion (draft revisions, severity re-calibrations, dropped findings) is invisible to them and never referenced in the body.

Cover, roughly in order:

1. **Disposition and why** — one prose sentence: right change at the right layer with one owner per responsibility, or shape needs revision / symptom-patch / net-zero / collision with parallel art? Cite the §3 gate ruling and root cause, not the comment count. Never open with the literal event token ("COMMENT." / "APPROVE."); GitHub already badges the review state, so the body starts with the *why*.
2. **Blockers** (`COMMENT` only) — the one or two findings that actually gate, each a numbered imperative ask naming the concrete mechanism: the exact test/fixture/flag to add, the invariant it must assert, the call site to move. Standard-protocol asks (test coverage, ticket reference, meeting a CI gate) are requirements, not requests — state them flatly. Never argue for them, pre-empt pushback, or plead the gate's legitimacy — real-vs-flake triage is evidence per point 3, stated once as fact, never a case for compliance. Detail that needs a paragraph belongs in the line comment; the verdict names the requirement. A supported structural ruling (`architecture-gate.md` "Ruling": a material defect shown in source plus one constraint-preserving correction) carries `COMMENT` on its own — the direction is the ask, stated as an imperative like any other blocker. On `revise`, add one sentence that review stopped at structure, name the unreviewed areas from §5, and state which body claims were not checked; never imply the rest is safe, and keep every serious defect already observed. Description findings are ordinary findings: the verdict names the missing or false material and the evidence that would settle it; it never rewrites the body. A required acceptance scenario in any state other than `passed` or `waived` (`acceptance.md` §4) is named in the body by its actual state and the limitation that remains — `failed` and `inconclusive` were exercised (state the observation and, for `failed`, its attribution or that attribution is unsettled); `not exercised`, `blocked`, and `not run — structure` were not — and holds the verdict at `COMMENT`; `APPROVE` needs every required scenario `passed` or `waived`, and a waiver is stated as an unverified limit, never as passed. If what remains is `opinion` without a named direction, or `suggestion`/`nit`, justify `COMMENT` over `APPROVE` — or flip.
3. **Evidence, woven in** — attach the probe or scenario to the claim it backs (*"the new tests fail on base for the stated reason"*; *"the workflow completes on head at the real entry"*), inline, as the observed fact, at the boundary it actually exercised. **Never the commands behind it**: CLI invocations, tool names, "Checks run:" paragraphs, CI counts, and sweep inventories are process narration that buries the findings. A probe that supports no specific claim doesn't appear.
4. **Headline opinion** — the unprompted call from **voice** (architecture, scope drift, missing invariant) that doesn't map to a line. Skip if none; don't pad.

Unrelated pre-existing defects discovered en route ("worth a ticket", fast-follows) go to a ticket or a PR conversation comment, not a verdict paragraph. That exclusion covers the defect finding only: a required acceptance scenario that `failed` with pre-existing attribution (same failure on base and head) stays in the verdict as an evidence and completeness limit — still required, unresolved until satisfied or waived, and never presented as a defect this PR introduced.

Shape: one ruling sentence, the numbered blockers, a short non-gating paragraph. A verdict longer than the diff is its own smell.

Once confirmed: hand off to `/post-review <PR>` with findings and verdict body (suggestion-block decisions live there — review judgment must not be biased toward apply-clickable issues). Posting appends the `post` notes entry (review id, comment ids → anchors) and refreshes the dossier per `dossier.md`.
