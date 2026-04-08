---
name: git-advanced
description: Advanced Git techniques for history editing, commit recovery, and cross-branch operations. Use when rebasing, cherry-picking, bisecting for bugs, recovering lost commits via reflog, splitting or squashing commits, or cleaning up history before a PR.
---

# Git Advanced Workflows

## Interactive Rebase

The primary tool for history editing.

**Operations:**

| Op | Effect |
|------|--------|
| `pick` | Keep commit as-is |
| `reword` | Change commit message |
| `edit` | Amend commit content |
| `squash` | Combine with previous commit (keep message) |
| `fixup` | Combine with previous commit (discard message) |
| `drop` | Remove commit |

```bash
# Rebase last N commits
git rebase -i HEAD~5

# Rebase all commits on branch vs main
git rebase -i $(git merge-base HEAD main)
```

### Autosquash

Automatically squash fixup commits during rebase:

```bash
git commit --fixup HEAD        # or --fixup <hash>
git rebase -i --autosquash main
```

### Split a Commit

```bash
git rebase -i HEAD~3           # mark commit with 'edit'
git reset HEAD^                # unstage but keep changes
git add file1.py && git commit -m "feat: add validation"
git add file2.py && git commit -m "feat: add error handling"
git rebase --continue
```

## Cherry-Picking

Apply specific commits across branches:

```bash
git cherry-pick abc123              # single commit
git cherry-pick abc123..def456      # range (exclusive start)
git cherry-pick -n abc123           # stage only, don't commit
git cherry-pick -e abc123           # edit message
```

### Partial Cherry-Pick (specific files only)

```bash
git checkout abc123 -- path/to/file1.py path/to/file2.py
git commit -m "cherry-pick: apply specific changes from abc123"
```

## Git Bisect

Binary search to find the commit that introduced a bug:

```bash
git bisect start
git bisect bad                     # current commit has the bug
git bisect good v1.0.0             # this commit was clean
# Git checks out a middle commit -- test it, then:
git bisect good                    # or: git bisect bad
# Repeat until found, then:
git bisect reset
```

### Automated Bisect

```bash
git bisect start HEAD v1.0.0
git bisect run ./test.sh           # exit 0 = good, 1-127 = bad
```

## Reflog (Recovery Safety Net)

Tracks all ref movements for ~90 days, including deleted commits:

```bash
git reflog                         # view all movements
git reflog show feature/branch     # specific branch

# Recover from accidental reset
git reflog                         # find the lost commit hash
git reset --hard abc123            # restore to it

# Recover deleted branch
git branch recovered-branch abc123
```

## Rebase vs Merge

| Use Rebase | Use Merge |
|------------|-----------|
| Cleaning up local commits before push | Integrating completed features into main |
| Keeping feature branch current with main | Preserving collaboration history |
| Creating linear history for review | Public branches used by others |

```bash
# Update feature branch with main (rebase)
git fetch origin
git rebase origin/main
# Handle conflicts, then: git rebase --continue

# Safe force push after rebase
git push --force-with-lease origin feature/branch
```

## Recovery Commands

```bash
# Abort in-progress operations
git rebase --abort
git merge --abort
git cherry-pick --abort
git bisect reset

# Undo last commit, keep changes
git reset --soft HEAD^

# Restore file from specific commit
git restore --source=abc123 path/to/file
```

## Best Practices

1. **Always `--force-with-lease`** over `--force` -- prevents overwriting others' work.
2. **Rebase only local commits** -- never rebase commits already pushed and shared.
3. **Backup branch before risky operations** -- `git branch backup-branch` before complex rebases.
4. **Atomic commits** -- each commit is a single logical change.
5. **Test after history rewrite** -- ensure rebase didn't break anything before force pushing.
