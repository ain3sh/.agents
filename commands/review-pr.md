---
description: Review a PR -- fetch context, analyze changes, post threaded review comments
argument-hint: <PR-number-or-URL>
---

Load skill: **pr-context**.

## 1. Gather Context

Follow the **pr-context** skill to fetch metadata, conversation, diff, linked Linear ticket, and derive repo identity / HEAD SHA from `$ARGUMENTS`.

## 2. Review

Analyze the changes **holistically** against these criteria:

1. **Goal achievement** -- Do the changes fully accomplish what the PR and/or ticket claim? Are there gaps between stated intent and actual implementation?
2. **Architectural brittleness** -- Are there fragile coupling points, implicit dependencies, or design decisions that will break under reasonable future changes?
3. **Code quality** -- Identify anti-patterns, poor naming, missing error handling, unnecessary complexity, suboptimal data structures or algorithms.
4. **Broader impact** -- How do the changes interact with the rest of the codebase? Look for missed edge cases, failure modes, race conditions, security concerns, or performance regressions.
5. **Test coverage** -- Are the changes adequately tested? Are there missing test cases for boundary conditions, error paths, or concurrent scenarios?

For each finding, note:
- **Severity**: critical / warning / suggestion / nit
- **File + line**: Exact location in the diff
- **What**: The specific issue
- **Why**: Why it matters
- **How**: Suggested fix or alternative (when applicable)

## 3. Post Threaded Review Comments

Use `REPO` and `HEAD_SHA` from the **pr-context** skill.

Post each finding as a **review comment on a specific line**:

```bash
gh api "repos/$REPO/pulls/<number>/comments" \
  --method POST \
  -f body="**[severity]** <comment>" \
  -f commit_id="$HEAD_SHA" \
  -f path="<file-path>" \
  -F line=<line-number> \
  -f side="RIGHT"
```

- Group closely-related findings into a single comment where it improves readability.
- Include the relevant code snippet in the comment body for context.

## 4. Verdict

After posting all line comments, submit a formal review:

- **Critical/warning issues found** -> `REQUEST_CHANGES` with a summary.
- **Only minor suggestions** -> `COMMENT` with a summary.
- **No issues** -> `APPROVE` with a brief positive note.

```bash
gh api "repos/$REPO/pulls/<number>/reviews" \
  --method POST \
  -f event="<REQUEST_CHANGES|COMMENT|APPROVE>" \
  -f body="<summary>"
```
