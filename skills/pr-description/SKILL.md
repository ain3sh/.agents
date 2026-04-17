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
- [ ] Four-section body: Description, Related Issue, Risk & Impact, Testing
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

## Potential Risk & Impact

<List specific risks, not generic boilerplate. Examples:>
<!-- - Changes the auth flow; existing sessions may need re-validation -->
<!-- - Adds a new DB index; migration will lock the table briefly -->
<!-- - Modifies a shared utility; downstream consumers should be tested -->
<!-- Use "Low risk -- isolated change with no external dependencies" only when genuinely true -->

## How Has This Been Tested?

<Describe concretely what was tested:>
<!-- - Unit tests added for X (describe coverage) -->
<!-- - Manual testing: did Y, observed Z -->
<!-- - Typecheck, lint, existing test suite passes -->
<!-- - Regression: verified old behavior still works by doing W -->
```

### Writing quality checklist

- The **Description** should make sense to someone who hasn't seen the ticket. Don't just restate the title.
- **Risk & Impact** must reflect actual thought about what could go wrong. "N/A" is acceptable only for truly zero-risk changes (typo fixes, comment-only changes).
- **Testing** should be specific enough that a reviewer can reproduce or verify.

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

Use dark-mode fills from `~/.agents/skills/excalidraw/references/dark-mode.md` combined with the semantic categories below. The first element in the array MUST be the massive dark background rectangle (`#1e1e2e`) so the canvas reads as dark mode even when opened in someone's light-mode Excalidraw.

| Component Type | Dark Fill | Stroke |
|----------------|-----------|--------|
| Frontend / UI | `#1e3a5f` | `#4a9eed` |
| Backend / API | `#1a4d2e` | `#22c55e` |
| Database / Storage | `#2d1b69` | `#8b5cf6` |
| Cloud / Infra | `#5c3d1a` | `#f59e0b` |
| Security / Auth | `#5c1a1a` | `#ef4444` |
| Message Bus / Queue | `#5c3d1a` | `#fb923c` |
| External / Generic | `#1a4d4d` | `#94a3b8` |

Text on dark: `#e5e5e5` for primary, `#a0a0a0` for secondary. Never use the default `#1e1e1e` stroke on dark -- it is invisible.

Workflow:

1. Write the `.excalidraw` file with the dark background rectangle as element 0.
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
   - **Testing gaps**: new code paths that aren't reflected in the "How Has This Been Tested?" section.

3. If none of the above apply, stop here -- no update needed. Do not rewrite for style or phrasing in this phase.

### Phase 2: Coherence pass

Only runs if Phase 1 identified updates. The goal is a description that reads as one authored piece, not a log of patches.

1. Draft the updated description incorporating the new material from Phase 1.
2. Before writing, check that the result:
   - Reads as a single coherent narrative about what the PR does and why -- not a chronological list of commits.
   - Preserves the four-section structure (Description, Related Issue, Risk & Impact, Testing).
   - Doesn't bloat: if the PR scope grew, the description should still be 2-4 sentences in the Description section, not a paragraph per commit.
   - Updates Risk & Impact to reflect the current full scope, not just the delta.
3. Apply the update via the REST endpoint documented in section 3b (**not** `gh pr edit` -- it currently fails on the Projects-classic GraphQL deprecation):
   ```bash
   REPO=$(gh repo view --json nameWithOwner --jq '.nameWithOwner')
   gh api "repos/$REPO/pulls/$PR_NUM" -X PATCH -f body="$(cat /tmp/pr-updated-body.md)"
   ```

**Do not** rewrite a description that is already accurate just because the phrasing could be marginally better. The bar for Phase 2 changes is: "a reviewer reading this description would get a wrong or incomplete picture of the PR."

**Do not** skip this refresh because the user did not explicitly ask for it. Any `git push` that lands on a branch with an open PR triggers Phase 1 automatically. Workflow commands (`/open-pr`, `/split-prs`, `/address-review`, `quality-ship`) are expected to run this flow as part of their normal completion -- they do not get to opt out.
