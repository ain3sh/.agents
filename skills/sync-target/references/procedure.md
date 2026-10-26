# Sync Target Procedure

## 0. Judge disposition

A clean sync proves Git can merge the branch, not that the PR still belongs.
Run the tripwires in bash with Detect's `TARGET_HEAD` and `FORK`.
`git merge-tree` previews the sync without touching the worktree; it leaves
only loose objects that `git gc` reclaims.

```bash
PR_FILES=$(git diff --name-only "$FORK" HEAD | sort)
MOVED=$(git diff --name-status --diff-filter=DR "$FORK" "$TARGET_HEAD" | cut -f2 | sort | comm -12 - <(printf '%s\n' "$PR_FILES"))
if SYNCED=$(git merge-tree --write-tree "$TARGET_HEAD" HEAD); then
  ABSORBED=$(git diff --name-only "$TARGET_HEAD" "$SYNCED" | sort | comm -13 - <(printf '%s\n' "$PR_FILES") | comm -23 - <(printf '%s\n' "$MOVED"))
else
  ABSORBED="unknown: the sync conflicts; classify the conflicts (§4) first"
fi
printf 'moved:\n%s\nabsorbed:\n%s\n' "$MOVED" "$ABSORBED"
```

| Tripwire | Evidence |
|---|---|
| Moved | `moved` lists a file the PR changes that the base deleted or renamed. |
| Absorbed | `absorbed` lists a file whose change the base already carries, so the synced PR would no longer change it. This catches cherry-picks and squashes alike. |
| Collision | A conflict or overlap resolution classifies as a genuine collision (§4, §5). |
| Asked | The user asks whether the PR still belongs: "modernize", "revive", "is this still needed". |

No tripwire: continue with the next step without comment.

When one fires, read the base commits behind it
(`git log --oneline "$FORK..$TARGET_HEAD" -- <paths>`) and the merged PRs
that carry them (`gh pr list --state merged --search <sha>`). Restate the
PR's smallest coherent goal from its title, body, and diff, then answer:

- Did the base already solve the same user-facing problem?
- Did the APIs, types, schemas, or boundaries the PR builds on change?
- Would landing it restore removed behavior or create a second way to do one
  job?
- Is the remaining benefit still worth its maintenance cost?

| Verdict | When | Move |
|---|---|---|
| SYNC | The goal is still useful and the shape still right. | Continue with the next step; report the tripwire and why it did not change the call. |
| REWORK | The goal is still useful, but syncing would preserve the wrong shape. | Stop before changing history. Report the smallest credible rewrite; proceed only once the user approves it. |
| CLOSE | The base absorbed, superseded, or invalidated the PR. Every PR file listed under `absorbed` is sufficient on its own. | Stop. Cite the commit or PR that did it. Never close the PR without the user. |

## 1. Judge stack propagation

```bash
CURRENT=$(git rev-parse --abbrev-ref HEAD)
stack status
```

If the current branch has an open stacked parent or descendant, load
**stack-cli** and inspect the affected stack:

```bash
stack sync "$CURRENT" # dry-run the affected stack
```

The preview is evidence, not an obligation to propagate. Decide:
load **stack-cli**'s `references/propagation.md` and follow its single decision
contract. If propagation is deferred, continue this procedure for the active
branch only.

If `stack` is unavailable, surface the missing inspection primitive rather
than guessing about stack scope.

## 2. Freeze the operation

Inspect the index, working tree, and untracked paths before changing history.
Leave unrelated work untouched when the chosen operation can safely preserve
it. If local work blocks the sync, scoped stash/restore is authorized
preparation, not a reason to ask again:

1. Record the exact paths, staged and unstaged changes, and untracked contents.
   Ensure no other writer is changing them; a branch backup does not preserve
   uncommitted work.
2. Stash only the necessary paths with `git stash push -- <paths>`; add
   `--include-untracked` only for explicitly selected untracked paths. Record
   the new stash's object ID and verify its contents before proceeding.
   Never stash the whole tree by reflex or include ignored files indiscriminately.
3. Own restoration on success, abort, or failure. After completing or aborting
   the Git operation, use `git stash apply --index <recorded-stash-oid>`, not
   `pop`, then verify content and staged/unstaged state against the record.
   Preserve local changes atop upstream changes; never overwrite the synced
   file with an old whole-file copy.
4. Retain the stash until restoration is verified. If application conflicts
   or recovery is uncertain, keep the recovery copy, hold the push, and resolve
   only what the recorded intent determines; ask for unresolved choices.
   Drop only this operation's verified stash, not a guessed `stash@{0}`.

Keep preserved user edits out of sync commits. Stop if work cannot be preserved
reliably or has concurrent ownership; do not discard it to obtain a clean tree.

```bash
CURRENT=$(git rev-parse --abbrev-ref HEAD)
REMOTE=$(git remote | head -1)
git fetch "$REMOTE" --prune

TARGET=$(printf '%s\n' $ARGUMENTS | grep -v '^--' | head -1)
[ -z "$TARGET" ] && TARGET=$(gh pr view --json baseRefName --jq .baseRefName 2>/dev/null)
[ -z "$TARGET" ] && TARGET=$(git symbolic-ref refs/remotes/"$REMOTE"/HEAD 2>/dev/null | sed "s|refs/remotes/$REMOTE/||")

TARGET_HEAD="$REMOTE/$TARGET"
LOCAL_HEAD=$(git rev-parse HEAD)
REMOTE_HEAD=$(git rev-parse "$REMOTE/$CURRENT" 2>/dev/null || true)
FORK=$(git merge-base "$TARGET_HEAD" HEAD)
BACKUP="sync-target/$CURRENT-$(date +%Y%m%d-%H%M%S)"
git branch "$BACKUP" "$LOCAL_HEAD"
```

Capture the PR context and frozen review shape:

```bash
INTENT_PATCH="/tmp/sync-target-$CURRENT-$$.patch"
gh pr view --json title,body,headRefName,baseRefName 2>/dev/null
git rev-list --first-parent --count "$FORK"..HEAD
git log --first-parent --reverse --format='%H %s' "$FORK"..HEAD
git diff --stat "$TARGET_HEAD"...HEAD
git diff --binary "$TARGET_HEAD"...HEAD > "$INTENT_PATCH"
```

Write down:

- the current and expected post-sync branch-only counts
- the ordered commit identities expected after the operation
- the source SHAs for every commit that belongs to the PR
- files and behavior the PR owns
- whether the branch was deliberately split, squashed, reordered, or rebuilt
- the cut commit immediately before the intended series, if replay is needed
- what upstream behavior must be preserved

The backup is the committed-history recovery source. Do not use
`git reset --hard`, checkout, or rebase until it exists and any local work the
operation would disturb has been preserved.

## 3. Choose one mode

### Merge mode

Use only when the branch's existing first-parent history is itself the intended
review history and no deliberate rewrite/split must be preserved.

Expected post-sync count is the frozen count plus one when Git creates a merge
commit. An already-up-to-date merge or fast-forward leaves the count unchanged.

```bash
git merge "$TARGET_HEAD" --no-edit
```

Merging is not justified merely because the repository squash-merges PRs. The
current PR's review surface still matters.

### Replay/rebase mode

Use when the branch was split, squashed, reordered, cherry-pick rebuilt, or the
expected branch-only series is smaller than the history currently reachable
from `HEAD`.

Expected post-sync count is the number of intended commits replayed.

Replay the explicit intended commits from the backup onto the target:

```bash
REPLAY="$CURRENT-sync-$(date +%Y%m%d-%H%M%S)"
git switch -c "$REPLAY" "$TARGET_HEAD"
git cherry-pick <oldest-intended-sha> ... <newest-intended-sha>
```

For one clean contiguous series, `git rebase --onto "$TARGET_HEAD" <cut>
"$CURRENT"` is equivalent. Do not use it when the range contains merged
predecessors, old sync commits, or other history that the split meant to drop.

After validation, move the original branch name to the replayed tip without
discarding the backup:

```bash
REPLAY_HEAD=$(git rev-parse HEAD)
git branch -f "$CURRENT" "$REPLAY_HEAD"
git switch "$CURRENT"
git branch -D "$REPLAY"
```

## 4. Resolve conflicts

Capture conflict paths before staging:

```bash
CONFLICTS=$(git diff --name-only --diff-filter=U)
```

For each file, read both sides in branch context and classify the resolution:

| Type | Action | Confidence |
|---|---|---|
| Non-overlapping | Integrate both | High |
| Superseding | Keep branch intent; adopt required upstream imports/types/dependencies | High if mechanical |
| Upstream improvement | Take target behavior | High if branch intent is unchanged |
| Genuine collision | Choose the intended business behavior | Low |

Continue the owning operation:

```bash
git add <resolved-paths>
git merge --continue        # merge mode
# or
git cherry-pick --continue  # replay via cherry-pick
# or
git rebase --continue       # replay via rebase
```

A genuine collision is a disposition tripwire: abort the operation
(`git merge --abort`, `git cherry-pick --abort`, or `git rebase --abort`) and
return to **Judge disposition** rather than improvising.

## 5. Audit silent auto-resolutions

Conflict markers are not the whole risk. Compute files both sides changed from
the pre-operation fork:

```bash
OVERLAP=$(comm -12 \
  <(git diff --name-only "$FORK" "$TARGET_HEAD" | sort) \
  <(git diff --name-only "$FORK" "$LOCAL_HEAD" | sort))
```

For each overlap file not already handled in `$CONFLICTS`, read the resulting
hunks and check for:

- duplicate definitions or guards
- references to symbols upstream renamed, moved, or deleted
- branch logic silently dropped by an auto-resolution
- upstream behavior silently reverted by the replay

Any semantic repair here is Low confidence and holds the push; one that
contradicts the PR's intent is a genuine collision (§4).

## 6. Prove the review shape

First verify the result's branch-only series:

```bash
git rev-list --first-parent --count "$TARGET_HEAD"..HEAD
git log --first-parent --reverse --format='%H %s' "$TARGET_HEAD"..HEAD
git diff --stat "$TARGET_HEAD"...HEAD
```

Compare the count, ordered identities, and PR diff with the operation-specific
expected shape. A normal merge adds one sync commit; replay does not. If a
four-commit split shows 24 commits, or merged predecessors/old sync commits
appear, the sync failed even when GitHub reports `MERGEABLE`.

When the intended source commits were contiguous, compare old and new intent:

```bash
git range-diff <cut>.."$LOCAL_HEAD" "$TARGET_HEAD"..HEAD
```

For a non-contiguous replay, inspect each replayed commit and the three-dot PR
diff against the recorded source SHAs. If the target did not move, also require
`git diff --exit-code "$LOCAL_HEAD" HEAD`. If it moved, account for every tree
delta; do not force equality by restoring old files wholesale.

## 7. Validate the combined result

Targeted scope is `$CONFLICTS + $OVERLAP`: every co-touched file, not the whole
target update. Run **quality-ship** with:

- per-file validators on every conflict/overlap path
- package-scoped typechecks and tests for the packages owning those paths

If the target changed an owning package without textual overlap, run the
smallest package-level integration check that can detect a broken combined
tree. Use `--full-scope` only when requested.

Load **worktree-setup** only after missing-module or empty-build-artifact
errors. Do not run `verify.py` proactively: its full-workspace manifest can
demand artifacts outside this sync's scope. Do not widen validation because the
worktree is stale.

Commit semantic repairs separately.

Restore any preserved local work using the recorded stash before the push gate.
Re-run affected checks if restoration changes validated paths, distinguishing
the committed sync result from the user's uncommitted changes.

## 8. Push gate

Hold if any:

- `$ARGUMENTS` contains `--no-push`
- the user said hold off this session
- preserved local work has not been restored and verified
- any conflict or auto-resolution is Low confidence
- the branch-only commit series differs from the frozen intended series
- the three-dot PR diff contains unexpected files or behavior
- the remote branch moved after `REMOTE_HEAD` was captured

Ordinary merge:

```bash
git push -u "$REMOTE" HEAD:"$CURRENT"
```

Rewritten history:

```bash
git push \
  --force-with-lease="refs/heads/$CURRENT:$REMOTE_HEAD" \
  "$REMOTE" HEAD:"$CURRENT"
```

If `REMOTE_HEAD` was empty, confirm the remote ref still does not exist before
creating it. Never replace an exact lease with bare `--force`.

## 9. Verify and report

Verify the remote SHA, PR base/head, branch-only commit count, mergeability, and
CI start. Report:

- tripwires fired and the disposition, or none
- target SHA and operation mode
- preserved expected commit series
- conflict and overlap paths
- High/Low confidence decisions
- validation commands and results
- pushed SHA or why the push is held
- backup branch name
- local-work restoration status and any retained stash object ID
