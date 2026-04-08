---
description: Full PR workflow -- ticket, branch, verify/fix, lint/test, commit, push, open PR
argument-hint: [TICKET-ID | description of work]
---

Load skills: **linear-cli**, **ticket-branch**, **quality-ship**, **pr-description**, **worktree-setup**.

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

If in a git worktree, follow the **worktree-setup** skill to symlink dependencies before running any checks.

Follow the **quality-ship** skill:
- Run all detected quality checks. Fix issues and re-run until clean.
- Commit (conventional format, referencing the ticket).
- Push.

## 4. Open PR

Follow the **pr-description** skill:
- Analyze the diff to determine change type, scope, and motivation.
- Format the PR title (conventional commits).
- Write the full PR body (all four sections: Description, Related Issue, Risk & Impact, Testing).

```bash
DEFAULT_BRANCH=$(git remote show origin 2>/dev/null | awk '/HEAD branch/ {print $NF}')
gh pr create \
  --base "$DEFAULT_BRANCH" \
  --title "<title>" \
  --body-file /tmp/pr-body.md
```

Report the PR URL.
