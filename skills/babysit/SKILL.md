---
name: babysit
description: Drive owned PRs to merge: watch CI and conflicts, address every review, keep the body excellent, and merge the moment it is approved.
argument-hint: "[PR-number-or-URL ...]"
disable-model-invocation: true
---

# Babysit

Own each target PR until it merges. Get it into approval shape, then get the
approval merged as soon as it lands. Invoking `/babysit` authorizes the routine
moves: fix, push, reply, resolve, sync, and merge. Bring the user only real
product or design decisions.

Targets: the PRs passed in, otherwise the current branch's PR.

Load skills: **pr-context**, **address-review**, **pr-description**,
**sync-target**, **quality-ship**, **voice**.

## Watch

Per PR, run one backgrounded watcher and one loop; never `sleep`+poll.

- **Watcher:** `gh pr checks <pr> --watch --fail-fast` as a `fireAndForget`
  Execute writing to a fixed log, with its pid and head sha recorded beside it
  (`.agents/babysit/<pr>.{log,pid,head}`).
- **Loop (`*/5`, head-agnostic):** read the log and the PR state; when the
  head sha moved or the watcher died, restart the watcher on the new head; then
  apply the table below. One loop covers every push. Cancel it, and the
  watcher, when the PR merges or closes.

## Act

Read state with `gh pr view <pr> --json reviewDecision,latestReviews,mergeable,mergeStateStatus,headRefOid` plus the watcher log.

| State | Move |
|---|---|
| CI failed | Read the failing job's log, load **root-cause-analysis**, fix through **quality-ship**, push. |
| Conflicts or behind base | **sync-target**. Stacked: **stack-cli**, merge bottom-up. |
| New review threads or comments, human or bot | **address-review**. This invocation confirms its `Fix`, `Respond`, and `Ack` rows; `Decline` rows and open product calls go to the user. |
| Any push | **pr-description** refresh: the body stays first-screen excellent, never a patch log. |
| `APPROVED`, green, mergeable, no unresolved threads | Merge with the repo's allowed method (`gh repo view --json squashMergeAllowed,mergeCommitAllowed,rebaseMergeAllowed`), confirm `MERGED`, stop the watcher and loop. |
| `BLOCKED` with none of the above | Check, in order: unresolved review threads, non-green required checks, merge conflicts, missing required reviewers. |

## Rules

1. A new commit does **not** dismiss prior reviews. Read `reviewDecision` and
   `latestReviews`; never infer review state from a push, and never re-request
   an approver.
2. Never devolve the PR's sleek excellence to clear a comment: no
   suppressions, no patch at the tagged line when the cause lives elsewhere,
   no body that narrates review rounds.
3. Repeated review rounds that keep finding issues are a red flag. Stop
   patching where feedback happens to be tagged: load **zoom-out**, find the
   root cause (**root-cause-analysis**, **patch-coherence**), and fix it at
   its layer.
4. Report only state changes: what moved, what you did, what waits on the user.
