# Sync Target Procedure

Every block is bash. §0 saves the run's state to a file and each later block
sources it first, so blocks may run in separate shells.

## 0. Set up

```bash
CURRENT=$(git rev-parse --abbrev-ref HEAD)
REMOTE=$(git remote | head -1)
git fetch "$REMOTE" --prune || exit 1

TARGET=$(printf '%s\n' $ARGUMENTS | grep -v '^--' | head -1)
[ -z "$TARGET" ] && TARGET=$(gh pr view --json baseRefName --jq .baseRefName 2>/dev/null)
[ -z "$TARGET" ] && TARGET=$(git symbolic-ref refs/remotes/"$REMOTE"/HEAD 2>/dev/null | sed "s|refs/remotes/$REMOTE/||")

TARGET_HEAD=$(git rev-parse --verify "$REMOTE/$TARGET^{commit}") || exit 1
LOCAL_HEAD=$(git rev-parse HEAD)
REMOTE_HEAD=$(git rev-parse --verify -q "$REMOTE/$CURRENT^{commit}")
if [ -n "$REMOTE_HEAD" ] && [ -n "$(git rev-list "$LOCAL_HEAD..$REMOTE_HEAD")" ]; then
  echo "$REMOTE/$CURRENT has commits this branch lacks; bring them in, then rerun §0"; exit 1
fi
FORK=$(git merge-base "$TARGET_HEAD" "$LOCAL_HEAD") || exit 1
BACKUP="sync-target/$CURRENT-$(date +%Y%m%d-%H%M%S)"
SCRATCH="$BACKUP-work"
ST=$(git rev-parse --absolute-git-dir)/sync-target
mkdir "$ST" || { echo "$ST exists: an earlier sync never finished; run its §10 first"; exit 1; }
git branch "$BACKUP" "$LOCAL_HEAD" || { rmdir "$ST"; exit 1; }
declare -p CURRENT REMOTE TARGET TARGET_HEAD LOCAL_HEAD REMOTE_HEAD FORK BACKUP SCRATCH ST > "$ST/env"
printf '%s@%.7s -> %s\n' "$REMOTE/$TARGET" "$TARGET_HEAD" "$CURRENT"
```

`$TARGET_HEAD` is a pinned SHA, so a later fetch cannot move the target
mid-run. Never hardcode `dev` or `main`. Stop only when the target is empty,
equals `$CURRENT`, or contradicts the user's request; otherwise the sync is
authorized, so carry on.

## 1. Preserve local work

```bash
. "$(git rev-parse --absolute-git-dir)/sync-target/env"
git status --porcelain --untracked-files=all
git diff --name-only "$FORK" "$TARGET_HEAD"
```

Local work blocks the sync when it touches a path the base changed or git
refuses the operation over it. Leave everything else untouched. Preserve
blocking work without asking:

1. Write its exact paths, staged and unstaged changes, and untracked contents
   to `$ST/record.md`, and make sure no other writer is changing them. The
   backup branch does not hold uncommitted work.
2. Stash only those paths with `git stash push -- <paths>`, adding
   `--include-untracked` for selected untracked paths and `--all` only for an
   ignored path you selected. Save the stash's object ID with
   `git rev-parse 'stash@{0}' > "$ST/stash"` and check its contents with
   `git stash show -p --include-untracked "$(cat "$ST/stash")"`.

If the work cannot be preserved reliably or has another owner, go to §10;
never discard it to get a clean tree. Keep preserved edits out of sync
commits.

## 2. Judge disposition

`git merge-tree` previews the sync without touching the worktree. The block
reads `$LOCAL_HEAD`, never `HEAD`, so it judges the PR even when §6 sends a
failed attempt back here.

```bash
. "$(git rev-parse --absolute-git-dir)/sync-target/env"
PR_FILES=$(git diff --name-only "$FORK" "$LOCAL_HEAD" | sort)
MOVED=$(git diff --name-status --diff-filter=DR "$FORK" "$TARGET_HEAD" | cut -f2 | sort | comm -12 - <(printf '%s\n' "$PR_FILES"))
printf 'moved:\n%s\n' "$MOVED"
if SYNCED=$(git merge-tree --write-tree --name-only "$TARGET_HEAD" "$LOCAL_HEAD"); then
  printf 'absorbed:\n'
  git diff --name-only "$TARGET_HEAD" "$SYNCED" | sort | comm -13 - <(printf '%s\n' "$PR_FILES") | comm -23 - <(printf '%s\n' "$MOVED")
else
  printf 'conflicts (absorbed cannot be computed; §6 classifies them):\n'
  printf '%s\n' "$SYNCED" | awk 'NR > 1 && !NF { exit } NR > 1'
fi
```

| Tripwire | Evidence |
|---|---|
| Moved | `moved` lists a file the PR changes that the base deleted or renamed. |
| Absorbed | `absorbed` lists a file whose change the base already carries, so the synced PR would no longer change it. This catches cherry-picks and squashes alike. |
| Collision | §6 classifies a conflict or overlap as a genuine collision. |
| Asked | The user asks whether the PR still belongs: "is this still needed", "should this still land", "revive it". |

No tripwire: go to §3.

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
| SYNC | The goal is still useful and its shape still fits the base. | §3. |
| REWORK | The goal is still useful, but syncing would keep a shape the base moved away from. | §3, with §5 Rework mode. |
| CLOSE | The base absorbed, superseded, or invalidated the PR. `absorbed` listing every file the PR changes is enough on its own. | `gh pr close "$CURRENT" --comment "<reason, citing the cause>"`, then §10. |

A partial `absorbed` list is SYNC when the rest of the PR stands on its own,
since the absorbed files simply leave the diff, and REWORK when the rest was
built on the absorbed part's old shape. A SYNC after a collision writes which
side's behavior wins to `$ST/record.md`, and §6 resolves the collision that
way instead of reopening it.

## 3. Judge stack propagation

```bash
. "$(git rev-parse --absolute-git-dir)/sync-target/env"
stack status
stack sync "$CURRENT"   # dry run
```

No open parent or descendant: go to §4. Otherwise decide with **stack-cli**'s
`references/propagation.md` whether descendants propagate, write the decision
to `$ST/record.md`, and sync the active branch here either way; §9 carries
out a propagation. Without `stack`, report the stack scope as unchecked.

## 4. Record the intended shape

```bash
. "$(git rev-parse --absolute-git-dir)/sync-target/env"
gh pr view --json title,body,headRefName,baseRefName 2>/dev/null
git log --first-parent --reverse --format='%H %s' "$FORK..$LOCAL_HEAD"
git diff --stat "$FORK" "$LOCAL_HEAD"
git diff --binary "$FORK" "$LOCAL_HEAD" > "$ST/intent.patch"
```

Append to `$ST/record.md`:

- The mode: Rework for a REWORK verdict; Replay under Rule 2 or when the
  intended series leaves out commits reachable from the branch; Merge
  otherwise.
- The source SHA of every commit that belongs to the PR. Merge commits are
  never among them; their PR-side changes arrive through the commits they
  merged.
- The files and behavior the PR owns, and the upstream behavior to preserve.
- The expected result. Series: merge adds one merge commit (none when the
  branch fast-forwards or is current); replay holds one commit per recorded
  source SHA, in order, minus any absorbed; rework holds new commits
  delivering the recorded behavior. Diff: `intent.patch` minus the absorbed
  files; for rework, the recorded behavior on the base's shape. §6 repair
  commits join the expected series as they land.

## 5. Sync

**Merge mode:**

```bash
. "$(git rev-parse --absolute-git-dir)/sync-target/env"
git merge "$TARGET_HEAD" -m "Merge $REMOTE/$TARGET into $CURRENT"
```

**Replay mode:** cherry-pick the recorded commits onto the target, oldest
first, on the scratch branch.

```bash
. "$(git rev-parse --absolute-git-dir)/sync-target/env"
git switch -c "$SCRATCH" "$TARGET_HEAD" && git cherry-pick <oldest-recorded-sha> ... <newest-recorded-sha>
```

A pick that comes out empty was absorbed: confirm its change is already in
the target, note its SHA as absorbed in `$ST/record.md`, and run
`git cherry-pick --skip`.

**Rework mode:** start the scratch branch, then re-implement the recorded
behavior against the current code. Keep the original commit messages and
authorship wherever they still describe the change.

```bash
. "$(git rev-parse --absolute-git-dir)/sync-target/env"
git switch -c "$SCRATCH" "$TARGET_HEAD"
```

## 6. Resolve and audit

At each stop, list the conflicts with `git diff --name-only --diff-filter=U`,
read both sides of each file in branch context, and classify it:

| Type | Action | Confidence |
|---|---|---|
| Non-overlapping | Integrate both | High |
| Superseding | Keep branch intent; adopt required upstream imports, types, and dependencies | High if mechanical |
| Upstream improvement | Take target behavior | High if branch intent is unchanged |
| Genuine collision | The sides want incompatible behavior, or resolving would grow the PR beyond §4's record or contradict its intent: go to **Collision** | — |

Write each path, its type, and its confidence to `$ST/record.md`, then
`git add <paths>` and `GIT_EDITOR=true git merge --continue` or
`GIT_EDITOR=true git cherry-pick --continue`.

Conflict markers are not the whole risk. When the operation finishes, list
every file both sides changed:

```bash
. "$(git rev-parse --absolute-git-dir)/sync-target/env"
comm -12 <(git diff --name-only "$FORK" "$TARGET_HEAD" | sort) \
         <(git diff --name-only "$FORK" "$LOCAL_HEAD" | sort) > "$ST/overlap"
```

In rework mode the list is every file the rebuilt series touches:
`git diff --name-only "$TARGET_HEAD" HEAD > "$ST/overlap"`.

In each overlap file not already read during conflict resolution, look for
duplicate definitions or guards, references to symbols upstream renamed,
moved, or deleted, branch logic an auto-resolution dropped, and upstream
behavior the sync reverted. A semantic repair is Low confidence until a §8
check that exercises it passes; commit it separately from the sync.

**Collision.** Undo the attempt, then return to §2 with the Collision
tripwire fired:

```bash
. "$(git rev-parse --absolute-git-dir)/sync-target/env"
git merge --abort 2>/dev/null; git cherry-pick --abort 2>/dev/null
git switch "$CURRENT" && git reset --merge "$LOCAL_HEAD" && { git branch -D "$SCRATCH" 2>/dev/null; true; }
```

`reset --merge` keeps the local edits §1 left in place; if it refuses, go to
§10 rather than discard them.

## 7. Prove the shape

```bash
. "$(git rev-parse --absolute-git-dir)/sync-target/env"
git log --first-parent --reverse --format='%H %s' "$TARGET_HEAD..HEAD"
git range-diff "$FORK..$LOCAL_HEAD" "$TARGET_HEAD..HEAD"
git diff --stat "$TARGET_HEAD...HEAD"
```

Apply Rule 1 to §4's expected series and diff. `range-diff` skips merge
commits; every `<` line must be a commit §4 left out or §5 found absorbed,
every pair `=` or a §6 resolution, and every `>` line a §6 repair. A
four-commit split that shows 24 commits is a failed sync: undo it as in
**Collision**, record Replay mode in §4, and redo §5 through §7. Account for
every other diff delta as an upstream change or a §6 resolution rather than
restoring old files wholesale.

In rework mode, check instead that each recorded behavior is delivered on
the base's shape and that the diff touches nothing the goal does not need.

## 8. Validate

Validate every path §6 recorded and every path in `$ST/overlap`, at their
final names, through **quality-ship**: per-file validators on each path, and
package-scoped typechecks and tests for the packages that own them. If the
target changed an owning package without textual overlap, run the smallest
package-level check that would catch a broken combined tree. Widen to
everything only with `--full-scope`; a stale worktree is not a reason to
widen. Do not run **worktree-setup**'s `verify.py` proactively: its
full-workspace manifest demands artifacts outside this sync.

## 9. Push

In replay and rework mode, move the branch name to the result:

```bash
. "$(git rev-parse --absolute-git-dir)/sync-target/env"
git branch -f "$CURRENT" HEAD && git switch "$CURRENT" && git branch -D "$SCRATCH"
```

Hold the push, and go to §10, when:

- `$ARGUMENTS` contains `--no-push`, or the user said to hold off
- any resolution is still Low confidence after §8

Every mode pushes the same way:

```bash
. "$(git rev-parse --absolute-git-dir)/sync-target/env"
git push --force-with-lease="refs/heads/$CURRENT:$REMOTE_HEAD" -u "$REMOTE" HEAD:"$CURRENT"
```

The lease passes only if the remote branch is still at `$REMOTE_HEAD`, or
still absent when that is empty. A rejection means someone pushed after §0:
run §10, bring their commits into the branch, and start over at §0.

After the push, carry out a propagation §3 decided on through
`propagation.md`'s **Propagate** step. A held push defers it.

## 10. Finish

Apply Rule 6. First stop anything this run left half done: abort a stopped
merge or cherry-pick and switch back to `$CURRENT`, keeping `$SCRATCH` for
the report. Then restore preserved work, never with `pop`:

```bash
. "$(git rev-parse --absolute-git-dir)/sync-target/env"
if [ -s "$ST/stash" ]; then git stash apply --index "$(cat "$ST/stash")"; fi
```

Verify content and staged state against §1's record, layering local edits
over upstream changes rather than restoring old whole-file copies. If the
restore conflicts, keep the stash and resolve only what the record
determines. Once the restore is verified, drop this stash by its recorded ID,
never a guessed `stash@{0}`:
`git stash drop "$(git stash list --format='%gd %H' | awk -v id="$(cat "$ST/stash")" '$2 == id { print $1 }')"`.
Re-run the checks for any validated path the restore touched, and report
them apart from §8's results: the pushed commit does not hold the restored
work.

Keep the backup branch. Delete `$ST` once the restore is verified; while a
restore or operation is unresolved, keep it and report the blocker.

Verify the remote SHA, PR base and head, commit count, mergeability, and
that CI started. Report the tripwires, the verdict, and the evidence behind
it, including why a SYNC verdict stood despite its tripwire; the target SHA
and mode; the commit series; the conflict and overlap paths with their
confidence; the validation results; the pushed SHA or why the push is held;
the stack decision; the backup branch; and the restore status with any
retained stash ID. For CLOSE, the close comment's URL replaces the push and
CI lines.
