---
name: sync-target
description: "Use when asked to sync, merge, rebase, update, or revive a PR branch from its base, or to resolve conflicts, while preserving the review shape."
argument-hint: "[--no-push] [--full-scope] [<target-branch>]"
---

# Sync Target

Bring a PR branch up to date with its base so it carries exactly the commits
and diff it claims, and decide whether it should still land at all when the
evidence says the base absorbed, moved, or collided with it.

Load skills: **pr-context**, **quality-ship**, **git-advanced**; **stack-cli**
when the branch has a stacked parent or descendants; **worktree-setup** only
after missing-module or empty-build-artifact errors.

## Act

Run `references/procedure.md` top to bottom; each step owns its commands.

| Step | Goal |
|---|---|
| §0 Set up | Resolve and pin the target, record the heads, back up the branch. |
| §1 Preserve local work | Stash only the local work the sync would disturb. |
| §2 Judge disposition | Run the tripwires; on a hit, rule SYNC, REWORK, or CLOSE. |
| §3 Judge stack propagation | Decide whether descendants propagate after the push. |
| §4 Record the intended shape | Write down the series and diff the result must carry. |
| §5 Sync | Merge, replay, or rework onto the target. |
| §6 Resolve and audit | Classify every conflict and every file both sides changed. |
| §7 Prove the shape | Compare the result with §4's record. |
| §8 Validate | Check the touched files and their packages. |
| §9 Push | Push through the gate, then propagate. |
| §10 Finish | Restore local work, clean up, and report. |

## Rules

1. Never call a sync done until the branch-only series and the PR diff match
   §4's record. GitHub's `MERGEABLE` only says the base can merge.
2. Never merge a branch that was split, squashed, reordered, or rebuilt:
   merging drags the dropped history back into review, and a later squash
   merge does not clean up the review surface now. Replay it.
3. Never rewrite history before §0's backup and §1's preservation exist, and
   never push without an exact lease.
4. Never open a disposition without a tripwire. Age, size, and distance behind
   the base weigh in once one is open; they never open one.
5. Never rule REWORK or CLOSE without the base commit or PR that caused it,
   and cite it in the rework's commit messages or the close comment.
6. Never leave by any exit, success, CLOSE, hold, or failure, without running
   §10.

## Failure map

| Symptom | Go to |
|---|---|
| `$TARGET_HEAD..HEAD` holds merged predecessors or old sync commits | §5 Replay mode. |
| The tree is right but the commit count is larger than planned | §7: the sync failed. |
| A clean merge with no conflict markers | §6 overlap audit. |
| A conflict or overlap turns out to be a genuine collision | §6 Collision. |
| The push lease is rejected | §9. |

## References

Load on demand; do not reabsorb into this file:

- `references/procedure.md`: every command and decision, step by step.
- `../stack-cli/references/propagation.md`: whether descendants propagate now.
