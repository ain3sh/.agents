---
name: babysit
description: Drive owned PRs to merge: watch CI and conflicts, address every review, keep the body excellent, and merge the moment it is approved.
argument-hint: "[PR-number-or-URL ...]"
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

One watcher per PR and nothing else: no `sleep`+poll, no cron loop. Run it as a
`fireAndForget` Execute:

```bash
~/.agents/skills/babysit/scripts/pr-watch <pr> [--repo owner/name]
```

It polls quietly and exits on the first poll that needs you, so its exit is the
wake-up. Output is event lines, then one verdict: `READY` or `MERGED` (exit 0),
`ACTION` or `CLOSED` (1), `ERROR` (2). The script's docstring defines every
event and the `READY` gate.

- Start it once the PR's current state is handled, and again in the same turn
  after every action (push, reply, sync). It remembers what it reported, so
  feedback that lands between runs arrives on the restart and nothing handled
  wakes you twice.
- A second watcher on the same PR exits 2 at once. Kill the first only if its
  exit can no longer reach you.

## Act

| Event or verdict | Move |
|---|---|
| `check-failed` | Read the failing job's log, load **root-cause-analysis**, fix through **quality-ship**, push. An `(optional)` failure the PR did not cause is a flake: rerun it (`gh run rerun <run-id> --failed`). |
| `conflict`, `behind`, `drift` | **sync-target** without asking. Stacked: **stack-cli**, merge bottom-up. |
| `comment`, `review`, `thread`, `reply`, `unresolved` | **address-review**. This invocation confirms its `Fix`, `Respond`, and `Ack` rows; `Decline` rows and open product calls go to the user. |
| Any push | **pr-description** refresh: the body stays first-screen excellent, never a patch log. |
| `READY` | Run `pr-watch <pr> --once`. On `READY`, merge with the repo's allowed method (`gh repo view --json squashMergeAllowed,mergeCommitAllowed,rebaseMergeAllowed`) pinned to the checked head (`gh pr merge <pr> --<method> --match-head-commit <sha>`), confirm `MERGED`, stop. On `ACTION`, handle its lines instead. |
| `blocked` | Check, in order: rulesets, required reviewers, merge queue, then `pr-context` for anything GitHub reports that the watcher does not model. |
| `MERGED`, `CLOSED` | Stop and report. |
| `ERROR` | Fix the input it names, or wait out GitHub, then restart the watcher. |

## Rules

1. A new commit does **not** dismiss prior reviews. Read `reviewDecision` and
   `latestReviews`; never infer review state from a push, and never re-request
   an approver.
2. Never merge on a stale `READY`. The `--once` run immediately before the
   merge is the gate: base commits since the fork point that touch the PR's
   files mean **sync-target** and fresh green checks first, because CI never
   tested them together.
3. Never devolve the PR's sleek excellence to clear a comment: no
   suppressions, no patch at the tagged line when the cause lives elsewhere,
   no body that narrates review rounds.
4. Repeated review rounds that keep finding issues are a red flag. Stop
   patching where feedback happens to be tagged: load **zoom-out**, find the
   root cause (**root-cause-analysis**, **patch-coherence**), and fix it at
   its layer.
5. Report only state changes: what moved, what you did, what waits on the user.
