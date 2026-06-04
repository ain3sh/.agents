---
name: pr-description
description: Shared atom for analyzing a diff and writing a structured PR description. Background knowledge for workflow commands -- not invoked directly.
user-invocable: false
---

# PR Description

## 0. When this skill fires (auto-activation)

Mandatory re-read **end-to-end** before any of: opening a PR (`gh pr create`, `/open-pr`, `/split-pr`); editing or refreshing a PR body/title; producing a draft for the user to paste manually. "I remember the structure" is not sufficient — load the skill every time.

**Pre-flight ritual.** Before the first `gh` call, emit this checklist in chat:

```
pr-description checklist:
- [ ] Diff analyzed (files, scope, change type)
- [ ] Title in conventional-commit format
- [ ] Body has 5 required sections + ticket linked (Closes / Part of, context-chain if relevant)
- [ ] Conditional sections from §0.5 catalog evaluated (each fired or skipped intentionally)
- [ ] Verification outcome-first; length ~250-450w; voice present-tense, third-person
- [ ] Using `gh api repos/$REPO/pulls/$N -X PATCH` for body/title (never `gh pr edit`)
```

Tick each as you work. A missing tick means the step is incomplete.

## 0.5. Section catalog

The 5 required sections fire on every PR. Conditional sections are a **menu, not a checklist** — if the trigger doesn't fire, the section doesn't exist in the body (empty "N/A" headings teach reviewers to skip). Templates: Section 5; architecture workflow: Section 4.

| Section | When |
|---|---|
| Description, Related Issue, Reviewer Guide, Risk & Impact, Verification | always |
| Anti-goals one-liner | scope deliberately constrained |
| Scope map + Out of scope | large or multi-concern diff where a reviewer could ask "why is this bundled?" (long-lived branch carrying merge alignment, plumbing + behavior + tests in one PR) |
| Implementation Notes | `.agents/specs/<spec>.notes.md` exists |
| Root Cause Analysis | bug fix |
| Architecture diagram | structural change (new components, altered flows, changed boundaries) |
| Schema / Contract Delta | DB / REST / GraphQL / protobuf / shared types touched |
| Migration & Rollout | flag / migration / env var / breaking API |
| Performance Evidence | perf-sensitive change |
| Telemetry & Observability | new/removed metrics, logs, traces, alerts |
| Repro Recipe | new feature / fixed bug — copy-pasteable verify steps |
| Side Effects | any acknowledged regression |
| Reverse Dependencies | >3 consumers of the changed surface |
| PR lineage | stacked / split chain |

## 1. Analyze the Diff

```bash
DEFAULT_BRANCH=$(git remote show origin 2>/dev/null | awk '/HEAD branch/ {print $NF}')
git log --oneline "origin/$DEFAULT_BRANCH"..HEAD
git diff --stat "origin/$DEFAULT_BRANCH"..HEAD
```

Extract **what** (touched dirs/packages), **type** (`feat`/`fix`/`refactor`/`docs`/`chore`/`test`/`perf`/`ci`/`build`/`revert`), **scope** (package/app in monorepos; module/layer otherwise), **why** (bug, feature, tech debt, perf).

## 2. Format PR Title

Conventional Commits: `type(scope): description`. Imperative ("add X", not "added X"); ≤72 chars. Comma-separate multi-scope (`fix(auth, api): ...`) or use a broader scope. If the repo defines valid scopes (CI config, CONTRIBUTING), use them exactly.

## 3. Write PR Body

Fill in **all five required sections**. Do not skip any.

```markdown
## Description

<2-4 sentences: what changed, why, and the high-level approach — intent and context a reviewer can't get from the diff. Mention non-obvious design decisions. Optional trailing one-liner: "Out of scope: <X> — tracked in TEAM-456." when scope was deliberately constrained.>

## Related Issue

Closes TEAM-123
<!-- "Closes" for full fixes, "Part of" for incremental work. Add a context chain (Slack thread, prior incident, design doc, related PR) only when prior art clarifies intent. -->

## Reviewer Guide

**Read order**: <file > file > file. Skip <noisy paths: snapshots, generated code>.>
**Review depth**: <Skim OK | Standard | Deep — one-line justification.>
**Open for pushback**: <one specific decision worth engaging, with a code anchor (`src/foo.ts:42`). Drop entirely if no live design call.>

## Risk & Impact

<Specific risks, not boilerplate. e.g., "Changes auth flow; existing sessions may need re-validation." or "New DB index; migration locks table briefly." "Low risk — isolated change" only when genuinely true.>

## Verification

**Behavior verified.** <User-visible flows exercised: state, action, observation. Tie back to listed risks.>
**Regression coverage.** <Test file/suite, invariant it pins, why this layer. For bug fixes, cite the consolidate-test-suites decision.>
**Not tested.** <Anything deliberately skipped + one-line reason. "N/A" only when genuinely true.>
**Standard validators.** <One line. e.g., "format/lint/knip/typecheck/full test suite clean." Note unrelated pre-existing failures and how you triaged them.>
```

### Writing quality

- **Description** stands alone for someone who hasn't seen the ticket; don't restate the title. Lead with the user-visible problem in plain words → why the current design can't simply be patched → what the PR does. Never open with internal vocabulary that only makes sense after reading the diff ("separate liveness from commit"-style one-liners draw "this needs a clear WHY" review comments) and never open with a non-goal ("the visual model is unchanged"). For large structural PRs the 2-4 sentence rule relaxes into a short **Why / What this PR does** pair (numbered mechanism steps are fine) plus a one-line net effect. If a design doc exists, link it at the end of the Description ("Full design rationale: [design doc](…)"), not only buried in Related Issue.
- **Naming**: title/prose terms must not collide with existing product surfaces (e.g., "stabilize transcript rendering" collided with the CLI's actual transcript alt-view → renamed to "stabilize chat rendering"). Use the product-accurate word in prose; reserve module/symbol names for code references.
- **Reviewer Guide** is the highest-leverage block. Order files by causal importance (not diff stat); drop the pushback line entirely when there's no live design call (empty prompts read as performative). When the diff contains intentional behavior changes that could read as drive-by edits or merge noise, add a **"Deliberate behavior changes (not merge noise):"** list — one line per change stating why the core change requires it.
- **Risk & Impact** reflects actual thought about what could go wrong. `N/A` only for typo / comment-only changes. For higher-risk PRs follow the risk bullets with a **"How risk is contained"** list (test counts, e2e matrix, before/after recordings, "no persistence/protocol change", single-revert restorability). Never claim a mitigation the diff doesn't contain — no "gated behind a flag" unless the flag exists in this PR; future rollout intent goes in Migration & Rollout, clearly marked as a plan.
- **Verification** is outcome-first; each block answers one reviewer question, and behavior-verified items tie back to listed risks so the two sections check each other. For enumerable behavioral changes use a `| Scenario | Before | After |` table — the "unchanged" rows show what you deliberately preserved.
- **Length** ~250-450 words baseline. Crossing 600 without an RCA / Architecture / Migration / Implementation Notes block in play usually means restating the diff — trim.
- **Voice** present-tense, indicative, third-person on the code ("This PR adds…", not "I added…"). First-person dates immediately.

### Stable searchable markers

Inline conventions (not their own section) — make PR bodies grep-able years later:

| Marker | Use when | Example |
|---|---|---|
| `Constraint from:` | external requirement imposed the design | `Constraint from: FAC-123 ("must work offline")` |
| `Decision-maker:` | non-obvious call made by a specific person | `Decision-maker: @alice (design review 2026-05-12)` |
| `As of:` | architecture-blame snapshot of the touched module | `As of: 2026-05-18 the cart module owns checkout redirects.` |
| `Sentinel test:` | canary that will fail first on regression | `Sentinel test: apps/web/test/checkout.test.ts:42` |

### What does NOT belong in Verification

CI already shows per-tool lint/typecheck/test status to reviewers. Re-listing it in the body buries the real signal (manual repros, regression coverage, deliberate skips). The `quality-ship` 6-row evidence checklist is for **gating the commit**, not for the PR body — resist copying it across.

**Anti-pattern** (representative bullets that should NOT appear):

- `ruff check, black --check, isort --check across the touched Python files - clean.`
- `npm run typecheck -- --filter=@factory/cli and npm run fix -- --filter=@factory/cli - both clean.`
- `npx prettier --check apps/cli/scripts/submit-eval.ts - clean.`

Compress them all into the single **Standard validators** line.

**Pattern** (same evidence, ordered for a reviewer):

> **Behavior verified.** Re-ran the upgraded run-evals path against PR #12292 with `tb2_smoke`; submission went through SQS and posted GitHub/Slack status. Surfaced a runtime-auth gap (stale worker `FACTORY_API_KEY`) which this PR fixes via per-message secret refresh.
>
> **Regression coverage.** Worker tests for per-eval secret refresh + failure handling (`src/eval_queue/tests/test_worker_update.py`, +20 cases); 109 passed, 2 skipped across the touched suites.
>
> **Not tested.** Three pre-existing failures (`test_ensure_http_toolkit_installs_and_starts`, `test_analyze_run_executes_successfully`, `test_default_s3_binary_download`) reproduce on base `dev` — apt/curl/SSO fixtures this PR doesn't touch.
>
> **Standard validators.** Format, lint, knip, typecheck, full test suite clean (Python + TS).

## 3b. Writing/updating the PR body: use REST, never `gh pr edit`

**Footgun.** `gh pr edit` currently fails on any repo whose org still has Projects (classic) enabled — the CLI issues a deprecated GraphQL query the server rejects:

```
GraphQL: Projects (classic) is being deprecated in favor of the new Projects experience, see: https://github.blog/changelog/...
```

Do not retry; it will not succeed until upstream `gh` ships a fix. Use the REST replacements below.

### Canonical REST replacements

Set once per session:

```bash
REPO=$(gh repo view --json nameWithOwner --jq '.nameWithOwner')
PR_NUM=$(gh pr view --json number --jq '.number')
```

| Operation | Use this | Not this |
|-----------|----------|----------|
| Update body | `gh api "repos/$REPO/pulls/$PR_NUM" -X PATCH -f body="$(cat /tmp/pr-body.md)"` | `gh pr edit --body` |
| Update title | `gh api "repos/$REPO/pulls/$PR_NUM" -X PATCH -f title="<new title>"` | `gh pr edit --title` |
| Add reviewer | `gh api "repos/$REPO/pulls/$PR_NUM/requested_reviewers" --method POST -f "reviewers[]=<login>"` | `gh pr edit --add-reviewer` |
| Add label | `gh api "repos/$REPO/issues/$PR_NUM/labels" --method POST -f "labels[]=<label>"` | `gh pr edit --add-label` |
| Set draft/ready | `gh api graphql -f query='mutation{ markPullRequestReadyForReview(input:{pullRequestId:"<node-id>"}){ pullRequest{ isDraft } } }'` | `gh pr ready` (also GraphQL-affected in some orgs) |

`gh pr create` and `gh pr view` are not affected — keep using them for initial creation and reads. Always write the body to a file first and pass `-f body="$(cat file)"` to avoid shell-quoting bugs with multi-line markdown, backticks, and `$`-escapes.

## 4. Optional Supporting Artifacts

Screenshots, short repro videos, before/after outputs, and small log snippets that clarify behavior or make validation easier. Upload via `gh-attach` when available; never include secrets, tokens, or machine-specific paths in uploaded artifacts or PR text. If the current machine lacks the browser-authenticated GitHub session, run `gh-attach` from a trusted machine (SSH is fine) or use `gh-attach --session-file`; keep the mention generic in public PRs.

### Architecture diagrams (dark-mode PNGs via excalirender)

When the PR adds/alters components, flows, service boundaries, integration points, or module structure, **draw it**. If you find yourself describing a new flow across more than two prose sentences of the Description, that's the signal.

**Quality bar — a diagram must carry information the prose can't.** Generic box-and-arrow renderings of the section headings get called out by reviewers as net-zero. What earns its place: real symbol/file names in the boxes, the data passed labeled on each arrow, and — for behavior changes — a concrete before/after timeline showing the old failure mode vs the new invariant across renders/requests, with example rows. After rendering, `Read` the PNG and check it: excalirender glyphs run wider than naive width estimates, so size boxes/label gaps generously and re-render until nothing overflows or collides.

**Non-negotiables**: render with `excalirender ... -o /tmp/diagram.png --dark -s 2` (bare editable-links don't embed and reviewers don't click); upload via `gh-attach` so the PNG lives at `user-attachments.githubusercontent.com` (never commit PNGs, never use `raw.githubusercontent.com`); skip `--dark` only when the user explicitly asks for light.

**Authoring rules** (see `~/.agents/skills/excalidraw/references/dark-mode.md` for the full failure modes):

- Author the `.excalidraw` in **light** theme — pastel fills from `~/.agents/skills/excalidraw/references/colors.md`, `#1e1e1e` text, `"viewBackgroundColor": "#ffffff"` or omit. `--dark` is an inverter; pre-coloring elements dark double-inverts into a washed-out render.
- **No manual background rectangle element** — it inflates the scene bbox and your diagram renders as a speck.
- Map components to the pastel families: Frontend/Input → Light Blue, Backend/Success → Light Green, Storage/Data → Light Teal, Processing/Middleware → Light Purple, Warning/External → Light Orange, Error/Critical → Light Red, Notes/Decisions → Light Yellow. `--dark` maps each to its matching dark variant at render time.

**Workflow**:

1. Write the `.excalidraw` (light colors, no background rect).
2. `excalirender diagram.excalidraw -o /tmp/diagram.png --dark -s 2`
3. `gh-attach --repo "$REPO" --md /tmp/diagram.png` — copy the returned markdown.
4. Optional editable-link companion: `uv run --with cryptography python ~/.agents/skills/excalidraw/scripts/upload.py diagram.excalidraw`
5. Embed under `## Architecture`; nest the editable link in `<details>` so it doesn't read as a phishing link:

   ```markdown
   ## Architecture

   ![Architecture](https://github.com/user-attachments/assets/...)

   <details>
   <summary>Edit diagram</summary>

   Source: https://excalidraw.com/#json=...
   Rendered: `excalirender diagram.excalidraw -o /tmp/diagram.png --dark -s 2`

   </details>
   ```

## 5. Conditional section templates

One template per catalog row. Use only the ones whose trigger fired; RCA and Implementation Notes live in `<details>` at the bottom so the body reads linearly.

### Implementation Notes — when `.agents/specs/<spec>.notes.md` exists

The `/implement` hook auto-scaffolds a paired notes file on spec approval. Locate it via the branch's ticket ID, then ingest:

```bash
TICKET=$(linear context --output json 2>/dev/null | jq -r '.identifier // empty' | tr '[:upper:]' '[:lower:]')
NOTES=$(ls .agents/specs/*.notes.md 2>/dev/null | rg -i "$TICKET" | head -1)
[ -n "$NOTES" ] && cat "$NOTES"
```

Group entries by their `Type:` field. Also thread them back into the always-on sections so they're not siloed: `deviation` → Description, `tradeoff` → Risk & Impact, `surprise` → Verification (Behavior verified), `followup` → Verification (Not tested) when relevant.

```markdown
<details>
<summary>Implementation Notes</summary>

Source: `.agents/specs/<basename>.notes.md`

**Deviations from spec**: <one bullet per `Type: deviation`>
**Tradeoffs**: <one per `Type: tradeoff` — alternative rejected + reason>
**Discovered constraints**: <one per `Type: surprise`>
**Follow-ups not in this PR**: <one per `Type: followup` — link tickets if filed>

</details>
```

If no notes file exists, this section does not appear.

### Root Cause Analysis — bug fixes

```markdown
<details>
<summary>Root Cause Analysis</summary>

**Trace**: <repro path, symptoms, investigation; cite artifacts pulled (Sentry IDs, log queries, bug reports)>
**Root cause**: <first unintended side effect — not the downstream error; name the broken invariant>
**Fix path**: <why this addresses the cause, not the symptom; the rejected symptom-level fix>
**Why this layer**: <if the fix isn't at the symptom's layer, justify; cite root-cause-analysis if it shaped the call>

</details>
```

### Anti-goals — scope deliberately constrained

One-liner under Description; prevents drive-by "while you're here…" comments:

```markdown
**Out of scope**: refactoring the legacy `auth/` module — tracked in TEAM-456.
```

Stack multiples as sub-bullets. If every PR has anti-goals, the scope was never honest to begin with.

### Scope map — large or multi-concern diffs

When a reviewer could reasonably ask "are unrelated changes bundled into this PR?", add a scope map at the end of the Description. One bullet per bucket: what it covers and why it must ship in this PR; close with an explicit Out of scope line.

```markdown
### Scope map — what is bundled and why

- **<bucket>** — <files/areas>. <one line: why the core change requires it.>
- **<bucket>** — …

**Out of scope:** <explicitly excluded work + where it's tracked / when it lands.>
```

Typical buckets: core change · metadata/plumbing it requires · deliberate behavior changes (cross-link the Reviewer Guide list) · tests/e2e · target-branch merge alignment ("no behavior of its own"). Bullets read better than a table when the "why" runs to a full sentence.

### Architecture — structural changes

See **Section 4** for the excalirender + dark + `gh-attach` workflow. Embed the rendered PNG under `## Architecture`; nest the editable link inside `<details>`.

### Schema / Contract Delta — DB / API / type contract touched

The 3 rows are a checklist; drop any that don't apply. Each row states the change + the backward-compat consequence in one line.

```markdown
## Contract Delta

**API**: <endpoint/method change; backward-compat note>
**DB**: <table/column/index change; migration safety>
**Types/SDK**: <type/symbol change; consumer compat>
```

### Migration & Rollout — flag / migration / breaking change

```markdown
## Migration & Rollout

**Order**: deploy (dark) → run `2026_05_18_add_redirected_to.sql` → flag `cart.redirect_v2` to 10% staging → verify dashboard → 100% staging → 10→100% prod over 24h.
**Rollback**: flag flip is sufficient up to 100%; migration is additive, no rollback needed.
**Coordination**: frontend `pr-1234` must merge first so the field is consumed before backend populates it.
```

### Performance Evidence — perf-sensitive changes

Numbers without methodology are theatre. Include workload, hardware, rerun command.

```markdown
## Performance Evidence

**Benchmark**: 10k `/checkout` requests, 100 concurrent, warm in-memory cart fixture (~500 items).
**Before** (`main` @ abc1234): p50 42ms / p95 81ms / p99 134ms; 1.4 cores avg; 3.2 MB/req.
**After** (this PR): p50 18ms / p95 31ms / p99 58ms; 0.6 cores avg; 0.8 MB/req.
**Conditions**: c6a.2xlarge, Node 22.4, `--max-old-space-size=4096`. Rerun: `pnpm bench:checkout`.
```

### Telemetry & Observability — metric / log / trace changes

```markdown
## Telemetry & Observability

**New**: <metric name + type (counter / histogram / gauge); what it measures>
**Changed**: <metric name + tag; impact on existing dashboards / alerts that filter on it>
**Logs**: <structured field + level + when emitted>
**Alerts**: <existing alert impact + any new alert candidate>
```

### Repro Recipe — new feature / fixed bug

The bar: a reviewer who has never touched this repo can run it as-is and observe the expected behavior.

```markdown
## Repro Recipe

```bash
pnpm dev
# Visit http://localhost:3000/cart, add 2 items, click checkout while logged out
# Expected: 302 redirect to /login?return_to=%2Fcheckout
```

Or: `pnpm test apps/web/e2e/checkout-redirect.spec.ts`.
```

### Side Effects — any acknowledged regression

Honest acknowledgment beats discovery six weeks later. If you genuinely can't think of any, the section does not appear — do not fabricate.

```markdown
## Side Effects

- Empty-cart users now see a ~50ms flash of the cart page before redirect (was an immediate 500). Acceptable per @alice — UX threshold 200ms.
- `cart_events` grows by ~1 row per checkout (was ~0 on the 500'd path). Est. +0.5% storage on the table over 90d.
```

### Reverse Dependencies — >3 consumers of the changed surface

✓ marks verified consumers (reviewers can stop reading); ⚠ marks owners to ping.

```markdown
## Reverse Dependencies

**Surface**: `@scope/sdk` `CheckoutClient.complete()` — added optional `onRedirect` callback.
**Consumers** (via `rg "CheckoutClient" -t ts`):
- ✓ `apps/web` — wired to new callback in this PR
- ✓ `apps/mobile` — ignores callback (optional)
- ✓ `services/order-worker` — ignores callback (server context)
- ⚠ `apps/admin` — owner @bob, not verified locally; optional callback preserves compat by type
- ⚠ `vendor-integration-x` — external; type-only change so compile-only consumers are safe
```

### PR lineage — stacked / split chain

```markdown
**PR lineage**: Part 3 of 5. Previous: #1234. Next: #1236. Tracks epic FAC-100.
**Type**: stacked (merge in order) | split (atomic — any order)
```

## 6. Post-Push Refresh

When a PR already exists and new commits have been pushed, run this two-phase check to keep the description accurate and coherent.

### Phase 1: Staleness check

Determine whether the existing description still covers what the PR actually does.

1. Fetch the current PR body and the new diff:
   ```bash
   PR_NUM=$(gh pr view --json number --jq '.number')
   gh pr view "$PR_NUM" --json title,body > /tmp/pr-current.json
   jq -r '.body' /tmp/pr-current.json > /tmp/pr-current-body.md
   DEFAULT_BRANCH=$(git remote show origin 2>/dev/null | awk '/HEAD branch/ {print $NF}')
   git log --oneline "origin/$DEFAULT_BRANCH"..HEAD
   git diff --stat "origin/$DEFAULT_BRANCH"..HEAD
   ```

2. Compare description against actual diff. Check for:
   - **Title drift** — title no longer matches the complete diff, violates `type(scope): description`, or exceeds 72 characters
   - **Missing scope** — new files/modules/packages not mentioned
   - **Changed intent** — original says "fix X" but diff also refactors Y
   - **Stale claims** — references to files/approaches/risks no longer applicable. Search absolute wording (`only`, `exact`, `complete`, `always`, `unchanged`, `lossless`) first: these claims decay fastest after follow-up commits.
   - **Evidence drift** — recordings, throwaway endpoints, fixtures, or pasted outputs are still described as proving the current behavior after their schema or source changed. Revalidate the artifact or weaken the claim to the narrower observation it actually proves.
   - **Generated appendix drift** — machine-generated or pasted appendices still match the latest diff. Search stable markers such as `<!-- *_START --> ... <!-- *_END -->`, semantic-diff `<details>` blocks, embedded snippets, diagrams, and generated file lists; regenerate or remove stale blocks rather than updating only the human-written summary.
   - **Verification gaps** — new code paths with no manual repro, no regression test cited, or unupdated **Not tested** note

3. If none apply, stop — no update needed. Do not rewrite for style or phrasing here.

### Phase 2: Coherence pass

Only runs if Phase 1 identified updates. The result should read as one authored piece, not a log of patches.

1. Draft the updated description incorporating Phase 1 material.
2. Before writing, verify:
   - Reads as a single narrative; Description still 2-4 sentences even on scope growth (use **Verification > Behavior verified** for added flows, not paragraph-per-commit).
   - Risk & Impact reflects current full scope, not just the delta.
   - Conditional sections re-evaluated — new commits may have crossed a threshold (e.g., >3 consumers → Reverse Dependencies; added a metric → Telemetry).
   - Every retained evidence claim is either revalidated against the current source or deliberately narrowed to a historically accurate observation.
   - Every retained generated appendix is regenerated from the current diff. If regeneration adds bulk without helping review, remove the appendix and replace it with a concise Reviewer Guide.
3. Apply via REST (see §3b — `gh pr edit` is broken):
   ```bash
   REPO=$(gh repo view --json nameWithOwner --jq '.nameWithOwner')
   gh api "repos/$REPO/pulls/$PR_NUM" -X PATCH -f body="$(cat /tmp/pr-updated-body.md)"
   ```
   If the title drifted, update it in the same pass:
   ```bash
   gh api "repos/$REPO/pulls/$PR_NUM" -X PATCH -f title="<type(scope): description>"
   ```

**Bar**: a reviewer reading the current description would get a wrong or incomplete picture. Don't rewrite for marginal phrasing wins. **Don't skip the refresh** because the user didn't ask — any `git push` onto a branch with an open PR triggers Phase 1, and `/open-pr`, `/split-pr`, `/address-review`, `quality-ship` run it as part of normal completion.
