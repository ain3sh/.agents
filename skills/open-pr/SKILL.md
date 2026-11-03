---
name: open-pr
description: "Use when the user asks to open, ship, land, or full-send a PR: ticket, branch, prove, commit, push, and open it from any starting state; land or full send drives it to merge."
argument-hint: "[TICKET-ID | description of work]"
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

## Full send

"Full send", "land it", or "send it" means the user is not watching: own the
work from its current state to a merged PR. Your updates go unread until long
after you stop. The request grants:

- every proof method step 2 needs, including ones a project rule says to ask
  about first (computer use, browser automation, running the app,
  screenshots); rules about *how* to test still bind;
- merging once `/babysit`'s gate passes, and `--force-with-lease` on this PR's
  own branch after a rebase.

It never grants deleting data, touching production, changes outside the repo,
closing a PR, force-pushing another branch, or bypassing branch protection.
Run steps 1–5.

Ask only when you cannot continue alone: the change cannot be proven, the
merge gate cannot pass and you cannot fix it, the next step falls outside the
grant, the goal is ambiguous in a way that changes the result, or another PR
makes this one obsolete. Ask in AGENTS.md's decision shape. Decide everything
else with a sensible default.

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

### Proof

Proof is evidence you observed in this session, as direct as the change
allows: reproduce the failure, apply the fix, and watch the same reproduction
pass; run the checks CI runs; when no test covers the behavior, add one
focused test that fails without the fix. For UI and runtime behavior, run the
app and look: green mocked tests do not prove the experience works. Every
change in the diff needs proof, and a change you cannot prove is one you are
not confident in.

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

Re-load `pr-description`, emit the Pre-flight checklist from its `references/workflow.md` inline, and tick every box before `gh pr create`. Drafting from memory is not allowed — "I remember the structure" is the exact failure mode this gate blocks.

Re-run the branch-name gate immediately before `gh pr create`. Do not open a PR from any branch except the exact expected idiomatic branch.

Finalize the body (`pr-description/references/publish.md`, Operations) before `gh pr create`, and run that file's round-trip verification after it. Finalize refuses a body without an Architecture view and stamps the `pr-desc-base` marker; a body without the marker skipped the hand-off.

```bash
DEFAULT_BRANCH=$(git remote show origin 2>/dev/null | awk '/HEAD branch/ {print $NF}')
gh pr create --base "$DEFAULT_BRANCH" --title "<title>" --body-file /tmp/pr-body.md
```

Report the opened PR as: `pr_title - pr_url`

## 5. Land (full send only)

Hand the PR to `/babysit` and stay with it until `MERGED`; prove each fix
before you push it. Then report the PR link, the merge commit, the proof, and
each decision you made for the user.
