---
name: sync-target
description: Sync a PR branch with its base while preserving review shape. Use when asked to sync, merge, rebase, update from main/dev/target, or resolve conflicts; merge ordinary branches and replay split/rewritten branches before validating and pushing.
argument-hint: [--no-push] [--full-scope] [<target-branch>]
---

# Sync Target

Sync the target without changing what the PR claims to contain.

Load skills: **pr-context**, **quality-ship**, **git-advanced**. If the branch
has a stacked parent or descendants, load **stack-cli** to inspect propagation;
apply it only when descendants need freshness now. Load **worktree-setup** only
for missing dependency/build-artifact failures.

## Act

| Goal | Action |
|---|---|
| Resolve the target | Explicit argument → open PR base → remote default; never hardcode `dev` or `main`. |
| Judge stack propagation | Run `stack status` and `stack sync <branch>`; either propagate with `stack-cli` or intentionally sync only the active branch and defer descendants. |
| Freeze the intended PR shape | Record the expected branch-only count, ordered commit identities, and diff before changing history. |
| Pick the operation | Merge ordinary published branches; replay/rebase branches already rewritten for a split or cleanup. |
| Resolve and audit | Inspect conflicts plus files changed by both sides; classify judgment calls. |
| Validate | Run `quality-ship` on every co-touched file and its owning package. |
| Gate the push | Refuse if the branch-only series or PR diff is not the recorded shape; use an exact lease for rewritten history. |

## Detect

```bash
CURRENT=$(git rev-parse --abbrev-ref HEAD)
REMOTE=$(git remote | head -1)
git fetch "$REMOTE" --prune

TARGET=$(printf '%s\n' $ARGUMENTS | grep -v '^--' | head -1)
[ -z "$TARGET" ] && TARGET=$(gh pr view --json baseRefName --jq .baseRefName 2>/dev/null)
[ -z "$TARGET" ] && TARGET=$(git symbolic-ref refs/remotes/"$REMOTE"/HEAD 2>/dev/null | sed "s|refs/remotes/$REMOTE/||")

TARGET_HEAD="$REMOTE/$TARGET"
FORK=$(git merge-base "$TARGET_HEAD" HEAD)

git rev-list --first-parent --count "$FORK"..HEAD
git log --first-parent --oneline "$FORK"..HEAD
git diff --stat "$TARGET_HEAD"...HEAD
```
If `$TARGET` is empty or equals `$CURRENT`, ask. Surface
`"$TARGET_HEAD" → "$CURRENT"` and confirm; stacked PRs miscall easily.

## Rules

1. Never use GitHub `MERGEABLE` as the success invariant—it proves the target
   can merge, not that the PR contains the intended commit series or diff.
2. Never merge by reflex after a split, squash, reorder, cherry-pick rebuild,
   or other deliberate rewrite—replay the recorded commits, not the polluted
   chain, onto the target.
3. Never propagate a stack merely because it exists. Compare descendant
   freshness needs with parent churn and repeated-restack cost.
4. Never justify extra branch history with the repository's landing strategy.
   Squash-merging the PR later does not repair a polluted review surface now.
5. Never push until both the branch-only count/ordered identities and PR diff
   match the frozen intent.
6. Never force-push without a backup and an exact lease; never auto-push a
   Low-confidence resolution.
7. Never apply a stack preview that mutates branches or PRs beyond the user's
   explicit scope; summarize the expansion and ask first.
8. Never leave deferred descendants implicitly stale. Name them, distrust their
   CI/diffs, and state the event that will trigger `stack sync --apply`.

## Failure map

| Symptom | Action |
|---|---|
| Parent is changing rapidly; descendants are dormant | Sync the active branch only, mark descendants intentionally stale, and defer `stack sync --apply`. |
| Descendant work/review/merge needs current parent behavior | Load `stack-cli`; preview the stack and apply the approved propagation. |
| Branch was just split or rewritten | Use `references/procedure.md` → **Replay/rebase mode**. |
| `origin/$TARGET..HEAD` shows merged predecessors or old sync commits | Stop; rebuild from the intended commit list rather than merging again. |
| Final tree is correct but commit count is larger than planned | Treat as failure; restore/rebuild before push. |
| Clean merge reports no conflict markers | Still audit the overlap set in `references/procedure.md`. |

## References

- Load on demand; do not reabsorb into this file:
  `references/procedure.md` — freeze packet, merge and replay commands,
  conflict/overlap audit, validation scope, topology gate, push, and report.
- Load on demand; do not reabsorb into this file:
  `../stack-cli/SKILL.md` — stack-wide inspection, repair, retargeting, and undo.
