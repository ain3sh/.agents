---
description: Full PR workflow -- ticket, branch, verify/fix, lint/test, commit, push, open PR
argument-hint: [TICKET-ID | description of work]
---

Load skills: **ticket-branch**, **quality-ship**.

## 1. Ticket + Branch

Follow the **ticket-branch** skill:
- If `$ARGUMENTS` contains a ticket ID, resolve it. Otherwise create one via `/open-ticket`.
- Check out a new branch off the default remote branch.

## 2. Apply Changes

First, determine the **entry state** -- does working code already exist from this session or another branch?

### If changes already exist

- **Uncommitted in working tree**: `git stash` before branch checkout in step 1, then `git stash pop` after.
- **On a different branch**: `git cherry-pick <commits>` or `git diff <branch> | git apply` onto the new branch.
- **Already verified this session** (bug repro'd, fix proven): skip to step 3.

### If starting fresh

- **Bug fix**: reproduce on base branch (confirm failure) -> apply fix on new branch -> verify fix (confirm pass).
- **Feature / enhancement**: implement on the new branch.

## 3. Quality + Ship

Follow the **quality-ship** skill:
- Run all detected quality checks. Fix issues and re-run until clean.
- Commit (conventional format, referencing the ticket).
- Push and open the PR.

Report the PR URL.
