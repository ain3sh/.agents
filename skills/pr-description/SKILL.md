---
name: pr-description
description: Shared atom for analyzing a diff and writing a structured PR description. Background knowledge for workflow commands -- not invoked directly.
user-invocable: false
---

# PR Description

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

### Architecture diagrams

When the PR introduces non-trivial architectural changes -- new components, altered data flows, changed service boundaries, new integration points, restructured modules -- generate a diagram using the **excalidraw** skill and link it in the PR body.

Use semantic colors for component types:

| Component Type | Excalidraw Fill | Stroke |
|----------------|-----------------|--------|
| Frontend / UI | `#a5d8ff` | `#4a9eed` |
| Backend / API | `#b2f2bb` | `#22c55e` |
| Database / Storage | `#d0bfff` | `#8b5cf6` |
| Cloud / Infra | `#fff3bf` | `#f59e0b` |
| Security / Auth | `#ffc9c9` | `#ef4444` |
| Message Bus / Queue | `#ffd8a8` | `#fb923c` |
| External / Generic | `#c3fae8` | `#94a3b8` |

Workflow:
1. Generate the `.excalidraw` file showing the relevant components and their relationships.
2. Upload via `python ~/.agents/skills/excalidraw/scripts/upload.py <file>` to get a shareable link.
3. Add the link to the PR body under a "Architecture" heading or inline in the Description.

Skip this when the change is purely behavioral (logic fixes, config tweaks, test additions) with no structural impact.

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
3. Apply the update:
   ```bash
   REPO=$(gh repo view --json nameWithOwner --jq '.nameWithOwner')
   gh api "repos/$REPO/pulls/$PR_NUM" -X PATCH -f body="$(cat /tmp/pr-updated-body.md)"
   ```

**Do not** rewrite a description that is already accurate just because the phrasing could be marginally better. The bar for Phase 2 changes is: "a reviewer reading this description would get a wrong or incomplete picture of the PR."
