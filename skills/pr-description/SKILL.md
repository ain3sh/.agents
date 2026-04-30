---
name: pr-description
description: Shared atom for analyzing a diff and writing a structured PR description. Background knowledge for workflow commands -- not invoked directly.
user-invocable: false
---

# PR Description

## 0. When this skill fires (auto-activation)

**This skill is mandatory -- not optional -- for every one of the following actions.** If you recognize any of these intents, you MUST re-read this skill end-to-end before producing any PR text or calling any `gh` command. "I remember the structure" is not sufficient; load the skill every time.

Triggering intents:

- Opening a new PR (`gh pr create`, `/open-pr`, `/split-prs`, or any equivalent).
- Editing or refreshing the body of an existing PR after pushing new commits.
- Updating a PR title.
- Adding the `Root Cause Analysis` section after a bug fix.
- Attaching architecture diagrams or other artifacts to a PR body.
- Producing a draft PR description for the user to paste manually.

**Pre-flight ritual.** Before the first `gh` call, emit the following checklist in chat so the user can see you are following conventions:

```
pr-description checklist:
- [ ] Analyzed diff (files, scope, change type)
- [ ] Title in conventional-commit format
- [ ] Four-section body: Description, Related Issue, Risk & Impact, Verification (outcome-first, not validator log)
- [ ] Linked ticket(s) with Closes/Part of
- [ ] RCA section for bug fixes
- [ ] Architecture diagram (excalirender, dark mode) for structural changes
- [ ] Using `gh api repos/$REPO/pulls/$N -X PATCH` for body/title updates (never `gh pr edit`)
```

Do not treat this as a ceremony. Tick each box as you work. A missing tick means the step is incomplete.

## 1. Analyze the Diff

Before writing anything, understand what changed:

```bash
DEFAULT_BRANCH=$(git remote show origin 2>/dev/null | awk '/HEAD branch/ {print $NF}')
git log --oneline "origin/$DEFAULT_BRANCH"..HEAD
git diff --stat "origin/$DEFAULT_BRANCH"..HEAD
```

Determine:
- **What changed**: Which directories, packages, or modules were modified.
- **Change type**: `feat`, `fix`, `refactor`, `docs`, `chore`, `test`, `perf`, `ci`, `build`, `revert`.
- **Scope**: Primary area affected. In monorepos, use the package/app name. In single-project repos, use the module or layer name.
- **Why it changed**: The motivation -- bug report, feature request, tech debt, performance issue.

## 2. Format PR Title

Conventional Commits: `type(scope): description`

- Keep the description concise and imperative ("add X", "fix Y", not "added X" or "fixes Y").
- For multi-scope changes, comma-separate: `fix(auth, api): ...` or use a broader scope.
- When the repo defines valid scopes (check CI config or contributing docs), use them exactly.

## 3. Write PR Body

Fill in **all four sections**. Do not skip any.

```markdown
## Description

<2-4 sentences: what changed, why, and the high-level approach.
Focus on intent and context a reviewer wouldn't get from the diff alone.
Mention any non-obvious design decisions.>

## Related Issue

Closes TEAM-123
<!-- Use "Closes" for full fixes, "Part of" for incremental work -->

## Risk & Impact

<List specific risks, not generic boilerplate. Examples:>
<!-- - Changes the auth flow; existing sessions may need re-validation -->
<!-- - Adds a new DB index; migration will lock the table briefly -->
<!-- - Modifies a shared utility; downstream consumers should be tested -->
<!-- Use "Low risk -- isolated change with no external dependencies" only when genuinely true -->

## Verification

**Behavior verified.** <Concrete user-visible flows exercised. For each: what state, what action, what was observed. Tie back to the risks called out in Risk & Impact so the two sections check each other.>

**Regression coverage.** <Which test file/suite, which invariant it pins, why this layer. For bug fixes, cite the consolidate-test-suites decision.>

**Not tested.** <Anything deliberately skipped, with a one-line reason. "N/A" only when genuinely true.>

**Standard validators.** <One line. e.g., "format/lint/knip/typecheck/full test suite clean." Note any unrelated pre-existing failures and how you triaged them.>
```

### Writing quality checklist

- The **Description** should make sense to someone who hasn't seen the ticket. Don't just restate the title.
- **Risk & Impact** must reflect actual thought about what could go wrong. "N/A" is acceptable only for truly zero-risk changes (typo fixes, comment-only changes).
- **Verification** is outcome-first: each of the four labeled blocks answers one reviewer question (behavior verified / regression coverage / not tested / standard validators). Tie each behavior-verified item back to a risk listed in **Risk & Impact** so the two sections check each other. See "What does NOT belong in Verification" below for what to keep out.

### What does NOT belong in Verification

CI status checks already show lint/typecheck/test results to reviewers; re-listing them per-tool in the PR body buries the actual signal (manual repros, regression coverage, deliberate skips) under a wall of "clean" status lines.

The six-row validator-evidence checklist that `quality-ship` enforces is for **gating the commit**, not the PR body. The agent's context window will be full of that checklist by the time it writes the description; resist the temptation to copy it across.

**Anti-pattern** -- representative bullets from real output that should NOT appear:

- `ruff check, black --check, isort --check across the touched Python files - clean.`
- `npm run typecheck -- --filter=@factory/cli and npm run fix -- --filter=@factory/cli - both clean.`
- `mypy across the touched evals source files - clean (Success: no issues found in 7 source files).`
- `npx prettier --check apps/cli/scripts/submit-eval.ts and bun build scripts/submit-eval.ts --outfile /tmp/submit-eval.js - clean.`

These tell a reviewer nothing about whether the change works. Compress them into the single **Standard validators** line.

**Pattern** -- what should appear instead (same PR, same evidence, reformatted):

> **Behavior verified.** Re-ran the upgraded run-evals path against PR #12292 with `tb2_smoke`; submission went through SQS and posted GitHub/Slack status. The rerun proved the HTTP Toolkit setup no longer raises `URLError`, and surfaced a separate runtime-auth gap (stale/missing worker `FACTORY_API_KEY`) which is fixed in this PR by per-message secret refresh. Reference experiment TOML validated end-to-end: `resolve_profiles()` produced two profiles (baseline, feature) with correct templates, feature-flag snapshots, and computed results dirs.
>
> **Regression coverage.** New worker tests for per-eval secret refresh + failure handling (`src/eval_queue/tests/test_worker_update.py`, +20 cases). Targeted module coverage across status round-trip / `wait_for_pickup`, experiment submit validation, env ghost-state, and HTTP Toolkit observability -- 109 passed, 2 skipped across the touched suites.
>
> **Not tested.** Three pre-existing failures in the full pytest run (`test_ensure_http_toolkit_installs_and_starts`, `test_analyze_run_executes_successfully`, `test_default_s3_binary_download`) reproduce on base `dev` -- they depend on apt/curl fixtures, ipykernel, and AWS SSO access, none of which this PR touches. Not addressed here.
>
> **Standard validators.** Format, lint, knip, typecheck, full test suite clean across both Python (ruff/black/isort/mypy/pytest) and TS (prettier/lint/typecheck/knip/bun build) sides.

Same evidence, ordered for a reviewer's eye, with validator chatter compressed to one line.

## 3b. Writing and updating the PR body: use REST, never `gh pr edit`

**Footgun:** `gh pr edit` currently fails on any repository whose org still has Projects (classic) enabled, even when you are not touching projects. The CLI issues a GraphQL query that the server rejects with:

```
GraphQL: Projects (classic) is being deprecated in favor of the new Projects experience, see: https://github.blog/changelog/...
```

This breaks `gh pr edit --body`, `gh pr edit --title`, `gh pr edit --add-reviewer`, and `gh pr edit --add-label`. **Do not retry it** -- it will not succeed until upstream `gh` ships a fix. Instead, go directly to REST.

### Canonical REST replacements

Set these once per session:

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

`gh pr create` and `gh pr view` are **not** affected -- keep using them for initial creation and reads.

Writing the body to a file and passing `-f body="$(cat file)"` avoids shell-quoting bugs with multi-line markdown, backticks, and `$`-escapes.

## 4. Optional Supporting Artifacts

When screenshots, videos, logs, or sample outputs would make the change easier to understand or verify, include them when practical.

- If `gh-attach` is available, upload supporting artifacts and link them in the PR body or a follow-up comment.
- Good candidates: UI screenshots, short repro videos, before/after outputs, and small log snippets that clarify behavior or make validation easier.
- Keep artifact references focused and high-signal; do not dump large noisy outputs into the PR body.
- Never include secrets, tokens, machine-specific paths, hostnames, or other private environment details in uploaded artifacts or PR text.

If the current machine cannot access the needed browser-authenticated GitHub session, it is acceptable to:

- run `gh-attach` from a trusted machine that does have that access, including over SSH, or
- use an exported `gh-attach --session-file` flow.

Keep any such mention generic in public PRs; describe the artifact itself, not your personal setup.

### Architecture diagrams (dark-mode PNGs via excalirender)

When the PR introduces non-trivial architectural changes -- new components, altered data flows, changed service boundaries, new integration points, restructured modules -- generate a diagram using the **excalidraw** skill and embed it inline in the PR body.

**Non-negotiable defaults**:

- **Always render with `excalirender`** (`excalirender diagram.excalidraw -o /tmp/diagram.png --dark -s 2`). A bare editable-link without an inline image does not count -- GitHub will not render it, and reviewers will not click through.
- **Always use dark mode** (`--dark`). Our PR descriptions are dark-first: the diagram must match so it does not blind a reviewer viewing on GitHub's dark theme. Skip dark mode only when the user has explicitly asked for light.
- **Always upload via `gh-attach`** so the PNG lives at `user-attachments.githubusercontent.com` -- never commit PNGs to the branch and never use `raw.githubusercontent.com` URLs.

**Author the `.excalidraw` in light theme** -- pastel fills from `~/.agents/skills/excalidraw/references/colors.md`, `#1e1e1e` text, `"viewBackgroundColor": "#ffffff"` (or omit). `--dark` is Excalidraw's theme inverter and expects a light source; pre-coloring elements dark (`#1e3a5f` fills, `#e5e5e5` text, dark `viewBackgroundColor`) double-inverts into a washed-out render. See `~/.agents/skills/excalidraw/references/dark-mode.md` for the full list of failure modes. **Do NOT add a manual background rectangle** element -- it inflates the scene bbox so the PNG balloons with your diagram as a speck.

Map components to the pastel families in `colors.md`: Frontend/Input -> Light Blue (`#a5d8ff`), Backend/Success -> Light Green (`#b2f2bb`), Storage/Data -> Light Teal (`#c3fae8`), Processing/Middleware -> Light Purple (`#d0bfff`), Warning/External -> Light Orange (`#ffd8a8`), Error/Critical -> Light Red (`#ffc9c9`), Notes/Decisions -> Light Yellow (`#fff3bf`). `--dark` maps each to its matching dark variant at render time.

Workflow:

1. Write the `.excalidraw` file in light colors. No background rectangle element, no dark `viewBackgroundColor`.
2. `excalirender diagram.excalidraw -o /tmp/diagram.png --dark -s 2`
3. `gh-attach --repo "$REPO" --md /tmp/diagram.png` -- copy the returned markdown.
4. Optional: `uv run --with cryptography python ~/.agents/skills/excalidraw/scripts/upload.py diagram.excalidraw` for an editable-link companion.
5. Put the image in the PR body under an "## Architecture" heading. Nest the editable link inside a `<details>` block so it does not look like a phishing link:

   ```markdown
   ## Architecture

   ![Architecture](https://github.com/user-attachments/assets/...)

   <details>
   <summary>Edit diagram</summary>

   Source: https://excalidraw.com/#json=...

   Rendered with: `excalirender diagram.excalidraw -o /tmp/diagram.png --dark -s 2`

   </details>
   ```

Skip this only when the change is purely behavioral (logic fixes, config tweaks, test additions) with no structural impact. If you find yourself describing a new flow in prose across more than two sentences of the Description, that is a signal you should be drawing it instead.

## 5. Contextual Additions

When the PR is part of a larger effort, add context:

- **Stacked PRs**: "Part K of N. Depends on #X." or "Independent -- can merge in any order."
- **Split from a branch**: "Splits `<original-branch>` into focused PRs. This one covers <scope>."
- **Follow-up work**: "Follow-up: <brief description of what's next>."
- **Bug fixes**: Append a collapsible "Root Cause Analysis" section to the PR body:

  ```markdown
  <details>
  <summary>Root Cause Analysis</summary>

  **How the bug was traced**: <Describe the repro path, the symptoms observed, and the
  investigation steps that narrowed down the root cause.>

  **How root cause drove the fix**: <Explain why the chosen fix addresses the actual cause
  rather than the symptom, and any alternatives considered.>

  </details>
  ```

## 6. Post-Push Refresh

When a PR already exists and new commits have been pushed, run this two-phase check to keep the description accurate and coherent.

### Phase 1: Staleness check

Determine whether the existing description still covers what the PR actually does.

1. Fetch the current PR body and the new diff:
   ```bash
   PR_NUM=$(gh pr view --json number --jq '.number')
   gh pr view "$PR_NUM" --json body --jq '.body' > /tmp/pr-current-body.md
   DEFAULT_BRANCH=$(git remote show origin 2>/dev/null | awk '/HEAD branch/ {print $NF}')
   git log --oneline "origin/$DEFAULT_BRANCH"..HEAD
   git diff --stat "origin/$DEFAULT_BRANCH"..HEAD
   ```

2. Compare the description against the actual diff. Check for:
   - **Missing scope**: new files, modules, or packages touched that the description doesn't mention.
   - **Changed intent**: the original description says "fix X" but the diff now also includes a refactor of Y.
   - **Stale claims**: the description references files, approaches, or risks that no longer apply after subsequent commits.
   - **Verification gaps**: new code paths that aren't reflected in the Verification section -- new behavior with no listed manual repro, new modules with no regression test cited, broadened scope without an updated **Not tested** note.

3. If none of the above apply, stop here -- no update needed. Do not rewrite for style or phrasing in this phase.

### Phase 2: Coherence pass

Only runs if Phase 1 identified updates. The goal is a description that reads as one authored piece, not a log of patches.

1. Draft the updated description incorporating the new material from Phase 1.
2. Before writing, check that the result:
   - Reads as a single coherent narrative about what the PR does and why -- not a chronological list of commits.
   - Preserves the four-section structure (Description, Related Issue, Risk & Impact, Verification).
   - Doesn't bloat: if the PR scope grew, the **Description** block should still be 2-4 sentences, not a paragraph per commit. Use **Verification** > **Behavior verified** to capture additional flows the broadened scope brought in.
   - Updates Risk & Impact to reflect the current full scope, not just the delta.
3. Apply the update via the REST endpoint documented in section 3b (**not** `gh pr edit` -- it currently fails on the Projects-classic GraphQL deprecation):
   ```bash
   REPO=$(gh repo view --json nameWithOwner --jq '.nameWithOwner')
   gh api "repos/$REPO/pulls/$PR_NUM" -X PATCH -f body="$(cat /tmp/pr-updated-body.md)"
   ```

**Do not** rewrite a description that is already accurate just because the phrasing could be marginally better. The bar for Phase 2 changes is: "a reviewer reading this description would get a wrong or incomplete picture of the PR."

**Do not** skip this refresh because the user did not explicitly ask for it. Any `git push` that lands on a branch with an open PR triggers Phase 1 automatically. Workflow commands (`/open-pr`, `/split-prs`, `/address-review`, `quality-ship`) are expected to run this flow as part of their normal completion -- they do not get to opt out.
