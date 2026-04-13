---
description: Fetch and merge latest remote dev into your branch, resolve conflicts in PR context
argument-hint: [--no-push]
---

Load skills: **pr-context**, **quality-ship**, **git-advanced**, **worktree-setup**.

## 1. Identify Branches

```bash
CURRENT=$(git rev-parse --abbrev-ref HEAD)
REMOTE=$(git remote | head -1)
git fetch "$REMOTE"
DEV=$(git branch -r | grep -oP "(?<=$REMOTE/)(dev|develop|development)$" | head -1)
```

If no dev branch found, ask the user. Confirm before proceeding.

## 2. Build Branch Context

Gather what this branch is doing so conflict resolution is informed:

```bash
gh pr view --json title,body,headRefName,baseRefName 2>/dev/null
git log --oneline "$REMOTE/$DEV".."$CURRENT"
git diff --stat "$REMOTE/$DEV".."$CURRENT"
```

Identify: which files this branch owns, what behavior it changes, what it should preserve from upstream.

## 3. Merge

```bash
git merge "$REMOTE/$DEV" --no-edit
```

If clean, skip to **step 5**. Otherwise list conflicts: `git diff --name-only --diff-filter=U`.

## 4. Resolve Conflicts

For each conflicted file, read both sides and **classify**:

| Type | Action |
|------|--------|
| **Non-overlapping** | Integrate both changes |
| **Superseding** | Keep ours; adopt new deps/imports/types from theirs |
| **Upstream improvement** | Take theirs |
| **Genuine collision** | Use judgment from branch context |

Stage each resolved file, then `git commit --no-edit`.

### Confidence tracking

Tag each resolution **High** (mechanical, clear intent) or **Low** (ambiguous, judgment call on business logic).

## 5. Quality Checks

Follow **quality-ship**: run all detected checks, fix issues, re-run until clean. Commit fixes separately if needed.

## 6. Push Gate

**Hold** (do NOT push) if ANY:
- `$ARGUMENTS` contains `--no-push`
- User instructed to hold off on pushing anywhere in this session
- Any resolution was **Low** confidence

When holding: summarize each conflict's resolution and confidence. For low-confidence ones, explain the ambiguity and the choice made. Ask whether to push or let the user review first.

**Auto-push** if ALL: no hold signals, all resolutions High (or no conflicts), quality checks passed.

```bash
git push -u origin HEAD
```
