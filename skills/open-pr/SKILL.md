---
name: open-pr
description: Full PR workflow -- ticket, branch, verify, lint, test, commit, push, open PR. Use when the user asks to open, ship, or land a PR; handles fresh work, mid-fix state, and changes already verified in the session.
argument-hint: [TICKET-ID | description of work]
---

Load skills: **linear-cli**, **ticket-branch**, **quality-ship**, **pr-description** (mandatory hand-off at step 4 — see below), **worktree-setup**.

## Todo cadence (non-optional)

At every `##` boundary:

1. Mark the prior section `completed` (only after verification).
2. Mark the incoming section `in_progress`.
3. Append newly-discovered subtasks as todos immediately.

After any approved spec or plan becomes ground truth (Phase 4 in `/implement`, equivalents elsewhere):

4. Rebuild the todo list against the spec -- one item per concrete deliverable (file edit, key decision, test, validator step). Structural placeholders give way to the atomic items they expand into.
5. The **final todo** is always: *"Re-read the spec; repopulate todos for any remaining stage, or mark the implementation complete."* This recursion anchors against context drift on long runs and chains multi-stage specs naturally -- do not skip it because the bottom of the list "feels done".

Fire `TodoWrite` in parallel with the first tool call of each phase.

## 1. Ticket + Branch

Follow the **ticket-branch** skill:
- If `$ARGUMENTS` contains a ticket ID, resolve it. Otherwise create one inline (ticket-branch handles both paths).
- Check out a new branch off the default remote branch. Ensure the current branch exactly matches the idiomatic ticket branch name. Worktree-created/default-derived names must be renamed, not carried into the PR.

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

### Branch-name gate (hard stop)

Before committing, pushing, or opening the PR, derive the expected branch name from the resolved ticket using the `ticket-branch` format: `<owner>/<prefix>-<number>-<stub>` (lowercase, hyphenated, ASCII-only, full name <= 32 chars).

```bash
CURRENT_BRANCH=$(git branch --show-current)
DEFAULT_BRANCH=$(git remote show origin 2>/dev/null | awk '/HEAD branch/ {print $NF}')
EXPECTED_BRANCH="<owner>/<prefix>-<number>-<stub>"
test "$CURRENT_BRANCH" = "$EXPECTED_BRANCH"
```

If the check fails, fix it before proceeding. Worktree-created/default-derived branch names are not exempt.

- If `CURRENT_BRANCH` is the default branch, create the idiomatic branch at the current HEAD: `git switch -c "$EXPECTED_BRANCH"`.
- Otherwise rename the local branch: `git branch -m "$EXPECTED_BRANCH"`.
- If the bad branch was already pushed, do not PR from it. The later push step must push the idiomatic branch with upstream: `git push -u origin "$EXPECTED_BRANCH"`. Do not delete the old remote branch unless the user explicitly asks.

Follow the **quality-ship** skill:
- Run all detected quality checks. Fix issues and re-run until clean.
- Commit (conventional format, referencing the ticket).
- Push.

## 4. Open PR — pr-description hand-off (mandatory)

Re-load `pr-description`, emit its section 0 checklist inline, and tick every box before `gh pr create`. Drafting from memory is not allowed — "I remember the structure" is the exact failure mode this gate blocks.

Re-run the branch-name gate immediately before `gh pr create`. Do not open a PR from any branch except the exact expected idiomatic branch.

```bash
DEFAULT_BRANCH=$(git remote show origin 2>/dev/null | awk '/HEAD branch/ {print $NF}')
gh pr create --base "$DEFAULT_BRANCH" --title "<title>" --body-file /tmp/pr-body.md
```

Report the opened PR as: `pr_title - pr_url`
