---
name: babysit
description: "Drive owned PRs to merge: watch CI and conflicts, address every review, keep the body excellent, and merge the moment it is approved."
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

Never `sleep`+poll, run a cron loop, or use `gh run watch` or
`gh pr checks --watch`, which poll REST every 3 seconds.

```bash
~/.agents/skills/babysit/scripts/pr-watch <pr> [--repo owner/name] [--once]
```

Output is event lines, then one verdict: `READY` or `MERGED` (exit 0),
`ACTION` or `CLOSED` (1), `ERROR` (2), and from `--once` only, `WAIT` (3). The
script's docstring defines every event and the `READY` gate.

What wakes you depends on where you run:

- **Cockpit change notices reach your session** (a cluster agent's do): the
  notice is your watcher. When you start, read each PR's current mark as your
  brief says, then run `pr-watch <url> --once` on each one you may act on; after
  that, on each PR a notice lists. Never start a blocking watcher: it
  polls GitHub every 300 seconds or slower on the budget the cockpit needs to
  detect changes, and it freezes when your computer pauses while you are idle.
- **Otherwise**, run `pr-watch <pr>` as a `fireAndForget` Execute, one per PR.
  It polls quietly and exits on the first poll that needs you, so its exit is
  the wake-up. Start it again in the same turn after every action (push,
  reply, sync). It remembers what it reported, so an item left open wakes you
  once; a first run reports everything open. A second watcher on the same PR
  exits 2 at once; kill the first only if its exit can no longer reach you.

What it reports:

- Feedback events are what is open on GitHub now: a thread that is unresolved
  and whose last comment is not your marked reply, outdated or not (a review
  drafted on an older commit arrives outdated), or a
  top-level comment or review posted, or edited by a human, after your latest
  marked reply. Bots and `factory-service-*` accounts rewrite status reports
  in place, so their edits never reopen anything. Comments from CI and
  deploy bots, from service accounts, and Linear's issue linkback are
  skipped outright.
  Only replies carrying `<!-- agent-reply -->` count as yours (address-review
  ends every reply with it); pushes, unmarked comments from your account, and
  replies still sitting in your pending review, which nobody else can read,
  never settle anything.
- Answered threads never wake you as feedback, but while unresolved they
  block `READY` through `unresolved`.
- `--once` reports everything open without reading or saving what it
  reported, though `MERGED` or `CLOSED` still deletes the watcher's state. It
  lists each failed optional check beside whatever verdict it gives. Run it
  whenever you need the PR's current state.

## Act

| Event or verdict | Move |
|---|---|
| `check-failed` | Read the failing job's log, load **root-cause-analysis**, fix through **quality-ship**, push. An `(optional)` failure the PR did not cause is a flake: rerun it (`gh run rerun <run-id> --failed`). When the only red is an `(optional)` check that also fails on the base branch or across many PRs, note it in the body and merge on the `--once` `READY`. `--once` lists optional failures beside any verdict: settle each here before you merge. |
| `conflict`, `behind` | **sync-target** without asking, including whatever disposition it rules. Stacked: **stack-cli**, merge bottom-up. |
| `comment`, `review`, `thread`, `unresolved` | **address-review**. This invocation confirms its `Fix`, `Respond`, and `Ack` rows; `Decline` rows and open product calls go to the user. |
| `pending-review` | Your account holds an unsubmitted review, and nobody else can read what is in it. The account is shared with the user, so the event alone does not say whose drafts these are: inspect them with **address-review** step 7's pending-review check, which submits or deletes the review only when its body, if non-empty, and every comment carry `<!-- agent-reply -->`. If any pending content lacks the mark, report it to the user and never submit or delete it. Re-run `pr-watch <pr> --once`. |
| Any push | **pr-description** refresh: the body stays first-screen excellent, never a patch log. |
| `READY` | Run `pr-watch <pr> --once`. On `READY`, merge with the repo's allowed method (`gh repo view --json squashMergeAllowed,mergeCommitAllowed,rebaseMergeAllowed`) pinned to the sha that verdict line ends with (`gh pr merge <pr> --<method> --match-head-commit <sha>`), confirm `MERGED`, stop. On `ACTION`, handle its lines instead; on `WAIT`, follow its row. |
| `WAIT` | After handling its event lines, start the watcher again, or under change notices, end the turn. |
| `blocked` | Check, in order: rulesets, required reviewers, merge queue, then `pr-context` for anything GitHub reports that the watcher does not model. |
| `MERGED`, `CLOSED` | Stop and report. |
| `ERROR` | Fix the input it names, or wait out GitHub, then run pr-watch again. |

## Rules

1. A new commit does **not** dismiss prior reviews. Read `reviewDecision` and
   `latestReviews`; never infer review state from a push, and never re-request
   an approver.
2. Never merge on a stale `READY`: the `--once` run immediately before the
   merge is the gate.
3. Never sync a PR the watcher has not flagged `conflict` or `behind`, even
   when base commits touch its files. A sync restarts CI and puts a PR that
   could merge now behind another run; GitHub flags `behind` whenever the
   base requires a current branch.
4. Never devolve the PR's sleek excellence to clear a comment: no
   suppressions, no patch at the tagged line when the cause lives elsewhere,
   no body that narrates review rounds.
5. Repeated review rounds that keep finding issues are a red flag. Stop
   patching where feedback happens to be tagged: load **zoom-out**, find the
   root cause (**root-cause-analysis**, **patch-coherence**), and fix it at
   its layer.
6. Report only state changes: what moved, what you did, what waits on the user.
