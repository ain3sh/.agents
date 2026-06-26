---
name: pr-description
description: Shared atom for analyzing a diff and writing a structured PR description. Background knowledge for workflow commands -- not invoked directly.
user-invocable: false
---

# PR Description

A PR description answers the reviewer's questions in the order they ask them, and front-loads what the diff can't give them: intent, the rejected alternative, the blast radius, and the proof it works. Every rule below derives from that.

## When this fires & how to load it

**Load this skill late — just-in-time, not as a flow preamble.** In a multi-step flow (`/open-pr`, `/split-pr`), finish the ticket, branch, verify, commit, and push steps *first*, then load it the moment before you create or PATCH the PR. Loaded early, the rules rot — by the time you write the body they're buried under everything you did since, and adherence slips. So **re-read from the file** right before any of: opening a PR (`gh pr create`); editing or refreshing a body/title; drafting a body to paste — the failure modes here are the ones agents misremember.

References load the same way — **one at a time, at the point of use.** The entrypoint is self-sufficient for a simple PR, so don't pre-read the table below; when a trigger fires and you're about to write that section, load that *one* reference, apply it, and move on. Read in a batch, each reference's signal dilutes in the noise; read the instant you apply it, each lands at full strength.

| Read | Load only when |
|---|---|
| `references/conditional-sections.md` | filling any non-required (conditional) text section |
| `references/visual-evidence.md` | the PR makes a concrete visual change (UI / TUI / CLI output / rendered media) — *after* the PR is open, to capture live proof without blocking the create |
| `references/artifacts.md` | a structural change (§3 row 2) — read it *before* deciding a diagram isn't warranted, not after; also the upload + caption mechanics for any screenshot / recording / diagram |
| `references/refresh.md` | the PR already exists and you're refreshing after a push |

**Pre-flight** (emit in chat, tick as you go):

```
pr-description checklist:
- [ ] Diff analyzed three-dot (§1); type/scope/why extracted
- [ ] Title: type(scope): imperative, <=72 chars
- [ ] 5 required sections present + ticket linked; catalog (§3) walked row by row
- [ ] Structural change? Architecture diagram drawn (references/artifacts.md) — default is *draw*, not skip
- [ ] Concrete visual change? Live proof captured via droid-control + attached high in body (references/visual-evidence.md) — *after* the PR is open, never blocking the create
- [ ] Verification outcome-first; CI status compressed to one line; length scaled to complexity
- [ ] Written via `gh api ... -X PATCH` (never `gh pr edit` — §5)
- [ ] Refresh only: base resolved + marker re-stamped (references/refresh.md)
```

## 1. Analyze the diff

```bash
DEFAULT_BRANCH=$(git remote show origin 2>/dev/null | awk '/HEAD branch/ {print $NF}')
git fetch -q origin "$DEFAULT_BRANCH"
git log  --oneline "origin/$DEFAULT_BRANCH"..HEAD    # two-dot: commits in HEAD, not base
git diff --stat    "origin/$DEFAULT_BRANCH"...HEAD   # three-dot: only what the branch introduced
```

**Three-dot (`...`) for every `git diff`, two-dot (`..`) for every `git log`.** Three-dot diffs from the merge-base — exactly GitHub's Files-changed tab. Two-dot diffs the endpoints, so it drags in changes that landed on the base after you forked (common on long-lived PRs). `git log` stays two-dot — a commit *list* wants exactly that asymmetric "in HEAD, not base" range. `git fetch` first so the merge-base is current.

Extract **what** (dirs/packages), **type** (`feat|fix|refactor|docs|chore|test|perf|ci|build|revert`), **scope** (package/app in monorepos; module/layer otherwise), **why** (bug, feature, debt, perf).

## 2. Title

`type(scope): description` — imperative ("add X", not "added X"), <=72 chars. Multi-scope: comma-separate (`fix(auth, api): …`) or broaden. Use the repo's declared scopes (CI config / CONTRIBUTING) verbatim if defined. On squash-merge repos the title becomes the permanent commit subject — weight it accordingly.

## 3. Body: sections, order, triggers

The 5 required sections fire on every PR. Conditional sections are a **menu, not a checklist** — if the trigger doesn't fire, the section doesn't exist (empty "N/A" headings train reviewers to skip). This table is the single source of truth for *what*, *when*, and *render order* (top to bottom). Conditional-row templates live in `references/conditional-sections.md`.

| # | Section | Fires when |
|---|---|---|
| 1 | Description | always — inline anti-goals / scope-map / design-doc link / Root Cause Analysis as needed |
| 2 | Architecture | structural change (new/altered components, flows, boundaries) → **draw** via `references/artifacts.md`; skip only when the diagram would add nothing prose can't (renders right after Description) |
| 3 | Visual Evidence | concrete visual change (UI / TUI / CLI output / rendered media) → capture live proof via `references/visual-evidence.md`; renders right after Architecture (or Description if no diagram). **Produced after the PR is open** so capture never blocks the create |
| 4 | Related Issue (+ PR lineage / stack block) | always; lineage line if stacked/split; stack block if `stack`-managed |
| 5 | Reviewer Guide | always |
| 6 | Risk & Impact | always |
| 7 | Contract Delta | DB / REST / GraphQL / protobuf / shared types touched |
| 8 | Migration & Rollout | flag / migration / env var / breaking API |
| 9 | Performance Evidence | perf-sensitive change |
| 10 | Telemetry & Observability | new/removed metrics, logs, traces, alerts |
| 11 | Reverse Dependencies | >3 consumers of the changed surface |
| 12 | Side Effects | acknowledged regression |
| 13 | Verification | always |
| 14 | Repro Recipe | new feature / fixed bug — **manual steps a human runs by hand, never a CI-run test command** |
| 15 | Implementation map | `<details>`; large multi-subsystem diff (~20+ files) |
| 16 | Changes since last review | `<details>`; refresh under active review → `references/refresh.md` |
| 17 | Implementation Notes | `<details>`; `.agents/specs/<spec>.notes.md` exists |

**Length scales with complexity, not effort.** A one-file fix is ~150 words and three sections. A complex PR earns length only through *conditional sections that carry real content* — the five required sections stay disciplined regardless. If the always-on body crosses ~450 words with no conditional block in play, you're restating the diff — trim.

**Live visual proof is the reviewer's trust layer (row 3).** When the diff changes what a human sees, a clip or screenshot from the running app lets a reviewer approve on sight instead of building and clicking — `references/visual-evidence.md` owns the capture decision tree. Run it *after* the PR is open so the multi-minute capture never blocks the create, then PATCH the artifact high in the body. If the capture surfaces a real bug, **stop and fail loud** — RCA it, don't ship over it.

### Required-section templates

```markdown
## Description

<2-4 sentences: the user-visible problem in plain words -> why the current design can't simply be patched -> what this PR does. Stands alone without the ticket; don't restate the title. Never open with internal vocabulary or with a non-goal. Large structural PR: relax into a **Why** / **What this PR does** pair (numbered mechanism steps OK) + a one-line "Net effect for users: …", and link the design doc here ("Full design rationale: [design doc]") — not only in Related Issue.>

## Related Issue

Closes TEAM-123   <!-- "Closes" full fix; "Part of" incremental. Add a context chain (thread / incident / design doc / prior PR) only when prior art clarifies intent. -->

## Reviewer Guide

**Read order**: file > file > file. Skip <snapshots, generated code>.
**Review depth**: Skim | Standard | Deep — one-line why.
**Open for pushback**: <one live design call + code anchor (`src/foo.ts:42`); drop the line entirely if none.>

## Risk & Impact

<Specific risks, not boilerplate ("changes auth flow; existing sessions may need re-validation"). "Low risk — isolated" only when true. Higher-risk PRs: follow with a "How risk is contained" list — test counts, e2e matrix, no persistence/protocol change, single-revert restorability.>

## Verification

**Behavior verified.** <flows exercised: state -> action -> observation; tie back to the listed risks. Anchor each claim to the commit checked (`verified @ <sha>`) so a refresh can detect staleness.>
**Regression coverage.** <test/suite + the invariant it pins + the failure mode(s) it proves (incl. any stress / adversarial / boundary case) + why this layer owns it; bug fixes and features both cite the consolidate-test-suites decision. Name the case that goes red on regression.>
**Not tested.** <deliberate skips, one reason **each**, held to a real skip bar (no harness / unreachable layer / genuinely contrived -- not "slow" or "hard to set up"); "N/A" only when true.>
**Standard validators.** <one line: "format/lint/typecheck/tests clean"; note unrelated pre-existing failures + how you triaged them.>
```

## 4. Writing quality

Load **voice** before drafting or editing this section and apply it to every line (specifics, named actors, no slop). Treat this as a required quality gate; the rules below are only the PR-specific additions.

- **Reviewer Guide is the highest-leverage block.** Order files by causal importance, not diff stat. Drop the pushback line when there's no live call — empty prompts read as performative. If intentional behavior changes could look like drive-by edits or merge noise, add a "Deliberate behavior changes (not merge noise):" list, one line each on why the core change requires it.
- **Description leads with the problem, not the mechanism.** "separate liveness from commit"-style openers draw "needs a clear WHY" comments; a non-goal opener ("the visual model is unchanged") buries the lede.
- **Naming**: prose terms must not collide with existing product surfaces (e.g., "transcript rendering" already meant the CLI's alt-view → use "chat rendering"). Reserve module/symbol names for code references.
- **Risk & Impact never claims a mitigation the diff doesn't contain** — no "gated behind a flag" unless the flag is in this PR. Future rollout intent goes in Migration & Rollout, marked as a plan.
- **Verification is outcome-first**; each block answers one reviewer question, and behavior-verified items tie back to listed risks so the two sections check each other. Enumerable changes → `| Scenario | Before | After |` table; the "unchanged" rows show what you deliberately preserved.
- **Voice**: present-tense, third-person on the code ("This PR adds…", not "I added…"). Date any first-person note.

**CI status does not belong in Verification.** Reviewers already see per-tool lint/type/test results in CI; re-listing them buries the real signal (manual repros, regression coverage, deliberate skips). Compress all of it to the one **Standard validators** line. (The `quality-ship` evidence checklist gates the *commit*, not the body.) Good shape:

> **Behavior verified.** Re-ran run-evals against PR #12292 with `tb2_smoke`; submission went through SQS and posted GitHub/Slack status — surfaced a stale-worker-key gap this PR fixes via per-message refresh.
> **Regression coverage.** Worker secret-refresh + failure tests (`src/eval_queue/tests/test_worker_update.py`, +20); 109 passed, 2 skipped.
> **Not tested.** Three failures reproduce on base `dev` (apt/curl/SSO fixtures untouched here).
> **Standard validators.** Format, lint, knip, typecheck, full suite clean (Py + TS).

### Stable searchable markers

Inline conventions (not their own section) — keep bodies grep-able years later:

| Marker | Use when |
|---|---|
| `Constraint from:` | an external requirement imposed the design (`Constraint from: FAC-123 ("must work offline")`) |
| `Decision-maker:` | a non-obvious call owned by a person (`Decision-maker: @alice (design review 2026-05-12)`) |
| `As of:` | architecture-blame snapshot of the touched module (`As of: 2026-05-18 cart owns checkout redirects`) |
| `Sentinel test:` | the canary that fails first on regression (`Sentinel test: apps/web/test/checkout.test.ts:42`) |
| `verified @` | pins a Behavior-verified claim to its commit (`verified @ a1b2c3d`); refresh flags it stale when newer commits touch the path |

## 5. Apply via REST — never `gh pr edit`

`gh pr edit` fails on any org with Projects (classic) enabled (it issues a deprecated GraphQL query the server rejects) — do not retry. Write the body to a file and PATCH it; `-f body="$(cat file)"` avoids quoting bugs with multi-line markdown, backticks, and `$`.

```bash
REPO=$(gh repo view --json nameWithOwner --jq '.nameWithOwner')
PR_NUM=$(gh pr view --json number --jq '.number')
```

| Operation | Use |
|---|---|
| Body | `gh api "repos/$REPO/pulls/$PR_NUM" -X PATCH -f body="$(cat /tmp/pr-body.md)"` |
| Title | `gh api "repos/$REPO/pulls/$PR_NUM" -X PATCH -f title="<title>"` |
| Reviewer | `gh api "repos/$REPO/pulls/$PR_NUM/requested_reviewers" -X POST -f "reviewers[]=<login>"` |
| Label | `gh api "repos/$REPO/issues/$PR_NUM/labels" -X POST -f "labels[]=<label>"` |
| Ready | `gh api graphql -f query='mutation{markPullRequestReadyForReview(input:{pullRequestId:"<node-id>"}){pullRequest{isDraft}}}'` |

`gh pr create` / `gh pr view` are unaffected — keep using them.

**Artifacts** (screenshots, recordings, diagrams): attach via `gh-attach` — never commit images, never embed secrets. Mechanics, recording captions, and the diagram workflow: `references/artifacts.md`.
