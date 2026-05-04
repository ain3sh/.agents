---
description: Review a PR -- typed verification + shared criteria, surface findings for approval; /post-review publishes.
argument-hint: <PR-number-or-URL>
---

Load skills: **pr-context**, **linear-cli**.

## 1. Gather Context

Follow **pr-context** to fetch metadata, conversation, diff, and linked Linear ticket; derive `REPO` and `HEAD_SHA` from `$ARGUMENTS`.

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

**Mandatory repro before code review** -- catches fixes that mask symptoms without addressing root cause.

1. Checkout base. Reproduce per ticket/PR description. Confirm failure.
2. Checkout PR branch. Re-run. Confirm fix.
3. Code-review with a **root-cause lens**: actual cause, or papering over a symptom? Right layer?

### Feature

1. Check against the ticket's acceptance criteria; flag gaps.
2. Evaluate API/UX design -- consistent with existing patterns? Will it age well?

### Refactor/chore

1. Verify **behavior preservation** -- no functional change unless explicitly stated.
2. Check for incomplete migration: missed renames, stale references, orphaned code.

### CI/Infra

1. Pipeline correctness and idempotency (safe to re-run?).
2. Secret handling, permissions scope, exposed surfaces.
3. Loosen code-style scrutiny on YAML/shell.

## 4. Shared Review Criteria

1. **Goal achievement** -- do the changes accomplish what the PR claims?
2. **Architectural brittleness** -- fragile coupling, implicit dependencies, decisions that break under future change?
3. **Code quality** -- anti-patterns, poor naming, missing error handling, unnecessary complexity?
4. **AI-slop (JS/TS only)** -- run `slop-scan` against base vs head worktrees and fold findings in. Treat hits (swallowed errors, placeholder comments, generic casts, pass-through wrappers, duplicate signatures, etc.) as real issues.

   ```bash
   BASE_REF=$(gh pr view <number> --json baseRefName --jq '.baseRefName')
   git fetch origin "$BASE_REF"
   BASE_SHA=$(git merge-base "origin/$BASE_REF" "$HEAD_SHA")
   BASE_WT=$(mktemp -d); HEAD_WT=$(mktemp -d)
   git worktree add --detach "$BASE_WT" "$BASE_SHA"
   git worktree add --detach "$HEAD_WT" "$HEAD_SHA"
   slop-scan delta "$BASE_WT" "$HEAD_WT" --json
   git worktree remove --force "$BASE_WT" && git worktree remove --force "$HEAD_WT"
   ```

   Install if missing: `npm install -g slop-scan`. Otherwise skip.
5. **Broader impact** -- missed edge cases, failure modes, race conditions, security, regressions?
6. **Test coverage** -- adequate? Missing boundary/error/concurrent cases?

For each finding record severity (`critical|warning|suggestion|nit`), file + line, and what/why/how.

## 5. User Approval Gate

Show every finding to the user before posting:

- Group by file; include severity, line, suggested fix.
- State intended verdict (`APPROVE` / `COMMENT`).
- Plain chat prose; **do not use `AskUser`** -- the user should be free to discuss, reword, drop, or re-severity findings.
- **Wait for explicit confirmation.** Apply any user edits before handoff.

Once confirmed, hand off to `/post-review <PR-number-or-URL>`. Suggestion-block decisions live there -- review judgment must not be biased toward apply-clickable issues.
