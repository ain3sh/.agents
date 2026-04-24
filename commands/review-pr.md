---
description: Review a PR -- classify type, verify per type, analyze changes, post threaded review comments
argument-hint: <PR-number-or-URL>
---

Load skills: **pr-context**, **linear-cli**.

## 1. Gather Context

Follow the **pr-context** skill to fetch metadata, conversation, diff, linked Linear ticket, and derive repo identity / HEAD SHA from `$ARGUMENTS`.

## 2. Classify PR Type

Infer the type from the PR title prefix, labels, linked ticket, and changed files:

| Type | Signals |
|------|---------|
| **Bug fix** | title `fix(...)`, label `bug`, ticket describes broken behavior |
| **Feature** | title `feat(...)`, label `feature`/`enhancement`, ticket describes new capability |
| **Refactor/chore** | title `refactor`/`chore`/`perf`/`docs`, no user-facing behavior change |
| **CI/Infra** | title `ci`/`build`, changes only in `.github/`, `infra/`, config files, scripts |

If ambiguous, default to **Feature**.

## 3. Type-Specific Verification

### Bug fix

**Mandatory repro before code review.** This catches fixes that mask symptoms without addressing root cause.

1. Checkout the base branch. Reproduce the bug using the steps from the ticket or PR description. Confirm the failure.
2. Checkout the PR branch. Run the same steps. Confirm the bug is resolved.
3. During code review, evaluate with a **root cause lens**: is this fixing the actual cause or papering over a symptom? Is the fix at the right layer?

### Feature

1. Check the implementation against the ticket's acceptance criteria point by point. Flag any gaps.
2. Evaluate API/UX design decisions -- are they consistent with existing patterns? Will they age well?

### Refactor/chore

1. Verify **behavior preservation** -- no functional change unless explicitly stated.
2. Check for incomplete migration: missed renames, stale references, orphaned code.

### CI/Infra

1. Check pipeline correctness and idempotency (safe to re-run?).
2. Review secret handling, permissions scope, and exposed surfaces.
3. De-emphasize code style criteria that don't apply to YAML/shell.

## 4. Shared Review Criteria

Apply to all types (framing adapts to the type above):

1. **Goal achievement** -- Do the changes accomplish what the PR claims?
2. **Architectural brittleness** -- Fragile coupling, implicit dependencies, decisions that break under future change?
3. **Code quality** -- Anti-patterns, poor naming, missing error handling, unnecessary complexity?
4. **AI-slop (JS/TS only)** -- Run `slop-scan delta <base-sha> <head-sha> --format json` on any PR touching JS/TS and fold its findings into the review. Score the 15 deterministic rules (swallowed errors, placeholder comments, generic casts, pass-through wrappers, duplicate signatures, etc.) as real issues, not nits. Skip only if `slop-scan` is unavailable (recommend install: `npm install -g slop-scan`).
5. **Broader impact** -- Missed edge cases, failure modes, race conditions, security concerns, regressions?
6. **Test coverage** -- Adequate tests? Missing boundary/error/concurrent cases?

For each finding, note:
- **Severity**: critical / warning / suggestion / nit
- **File + line**: Exact location in the diff
- **What/Why/How**: The issue, why it matters, suggested fix

## 5. User Approval Gate

Present all findings to the user before posting anything to GitHub:

- List each finding grouped by file, with severity, line, and suggested fix.
- State the intended verdict (`APPROVE` / `COMMENT` / `REQUEST_CHANGES`).
- Present this in normal chat prose; **do not use `AskUser`** for the review report. The goal is to let the user discuss, reword, drop, or re-severity findings naturally before anything is posted.
- **Wait for explicit user confirmation** before proceeding to step 6.

If the user edits, drops, or re-severities any findings, apply those changes before posting.

## 6. Post Threaded Review Comments

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
- When the user approves posting a suggestion and the fix is small, mechanical, and line-local, include a GitHub direct-apply suggestion block:

  ````markdown
  ```suggestion
  <replacement code>
  ```
  ````

  Use this only at posting time. Do not let the possibility of an applyable suggestion bias the review toward recommending changes; first decide whether the issue is worth raising, then decide whether a suggestion block would help the author apply it safely.
- Prefer `--input /tmp/comment.json` for comments containing suggestion blocks, backticks, JSON, or other shell-sensitive text.

## 7. Verdict

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
