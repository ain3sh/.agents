---
description: Break a branch's commits into clean, separate PRs
argument-hint: <branch-name> [--base <base-branch>]
---

Load skills: **ticket-branch**, **quality-ship**.

## 1. Analyze the Branch

```bash
DEFAULT_BRANCH=$(git remote show origin 2>/dev/null | awk '/HEAD branch/ {print $NF}')
BASE="${base:-$DEFAULT_BRANCH}"
git log --oneline "$BASE".."$BRANCH"
git diff --stat "$BASE".."$BRANCH"
```

For each commit, collect:
- Files changed and their packages/directories.
- Whether it's a logical unit (single concern) or a grab-bag.
- Dependencies on other commits (does commit B only make sense after commit A?).

## 2. Propose Split Plan

Group commits into proposed PRs by logical concern (feature area, package, layer). For each proposed PR, list:
- **Title**: conventional commit style.
- **Commits**: which commits (by SHA short) it includes.
- **Files**: directories/packages touched.
- **Dependencies**: which other proposed PRs must land first (if any).

### Stacking Decision

Evaluate file overlap between proposed PRs:
- **No overlap** (each PR touches disjoint files): use **independent PRs** targeting the base branch. Can merge in any order.
- **Overlap exists** (multiple PRs modify the same files): use **stacked PRs** where each targets the previous PR's branch. Must merge in order.

Flag any commits that span multiple proposed PRs (conflict risk). Suggest rewriting or splitting those commits if feasible.

**Present the plan and wait for user approval** before executing.

## 3. Execute the Split

For each proposed PR, in dependency order:

### Create branch
```bash
# Independent: branch off base
git checkout -b "ain3sh/<prefix>-<number>-<stub>" "origin/$BASE"

# Stacked: branch off previous PR's branch
git checkout -b "ain3sh/<prefix>-<number>-<stub>" "<previous-pr-branch>"
```

### Apply commits

**Always move code via git operations (cherry-pick, stash, diff-apply), never manually re-type changes.** Manual re-implementation risks introducing drift from the original work and wastes time. Only fall back to manual edits for edge cases where git operations genuinely can't produce the right result (e.g., a commit must be decomposed at the hunk level and cherry-pick -p isn't sufficient).

- **Clean commits** (single concern, no overlap): `git cherry-pick <sha1> <sha2> ...`
- **Tangled commits** (overlap across PRs): `git cherry-pick --no-commit`, then selectively stage relevant hunks with `git add -p`, discard the rest.
- **Partial file moves**: `git diff <sha>~1..<sha> -- <paths> | git apply` to extract only specific file changes from a commit.
- If cherry-pick conflicts arise, resolve them. If unresolvable, flag to the user.

### Quality checks + push
Follow the **quality-ship** skill: run detected checks, fix issues, commit any fixups, push.

### Open PR
```bash
gh pr create \
  --base "$TARGET" \
  --title "<title>" \
  --body "<body>"
```

PR body should include:
- **Context**: "Part K of N from [ticket/branch]. Splits [original-branch] into focused PRs."
- **Dependencies**: "Depends on #X" or "Independent -- can merge in any order."
- **What this PR covers**: brief scope description.

## 4. Report

List all created PRs with their URLs, dependency graph, and recommended merge order.
