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
