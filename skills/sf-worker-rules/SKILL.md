---
name: sf-worker-rules
description: Operating rules for headless Software Factory workstream runs on Ainesh's behalf (intake, triage, investigate, implement, steward, steward sweep, health). Use at the start of every such run, before reading sources or changing anything.
---

# Software Factory Worker Rules

No human is present. These rules stand in for the judgment Ainesh would apply
mid-run. The workstream's own skill owns its procedure; this skill owns how
every procedure is carried out. When they conflict, the workstream skill wins
on *what* to do and these rules win on *how carefully*. One exception: the
Software Factory defect report below applies in every stage, including stages
that otherwise forbid posting outside the workstream.

## Act

| Moment | Action |
|---|---|
| Run starts | Run the workstream's `scripts/setup-run.sh`. Then state in one sentence what this run must achieve and the observable condition that proves it. |
| Reading state | Read through the workstream's reader script when it has one. Act only on what it printed. |
| Planning a fix | Preregister the success test: the exact command or reader line that must flip, before editing anything. |
| A non-trivial diff is ready | Get an adversarial review from the `astra` droid on the full diff plus the plan. Fix or rebut every finding with evidence before pushing. |
| After every outward write | Re-read the target and confirm the write landed (see rule 4). |
| Run ends | Re-read state and check it against the sentence from run start: each condition done or not done, with evidence. Unfinished work gets a concrete next step in memory. |

## Rules

1. **Unknown is not clean.** A failed, partial, or errored read is a failure to
   report, never "nothing to do". Never hide stderr (`2>/dev/null`, `|| true`)
   on a read you act on.
2. **One reader per state.** Every stage reads through the same reader. If it
   is wrong or missing a field, fix the reader (rule 8); never query around it.
3. **Name exact things.** PR numbers, check names, `file:line`, thread URLs,
   SHAs. Never "some checks fail" or "a few comments".
4. **Done means re-read.** A push is done when the remote head equals your
   local SHA. A thread is done when it reads resolved. A rerun is done when the
   check shows queued or running. A message is done when it appears in the
   history. If verification fails, re-read before retrying: never resend a
   write that may have landed.
5. **Preregister.** Write the success test before the change, then report it
   as passed or failed. Never redefine success after seeing the result.
6. **Adversarial review for non-trivial diffs.** Non-trivial means anything
   beyond a mechanical change (format-only, lockfile regeneration, a clean
   merge of the base). The reviewer gets the diff, the plan, and the
   preregistered test.
7. **Findings end with an action.** Say who should do what, with the URL.
   Report a blocked item once (check existing events first) and do not repeat
   it each run.
8. **Fix the harness first.** When a script, skill, or memory note misled you,
   correct `scripts/` in this run if the fix is small and you validate it on
   live data; otherwise record a warning event naming the defect and the fix.
   Never quietly work around it.
9. **Cost never vetoes needed work.** Do not skip a needed rerun, review, or
   validation to save time or tokens. Do skip work that is not needed.
10. **Decide routine calls yourself; stop on material ones.** Make obvious
    in-scope judgment calls without asking. When a material contract or a
    review verdict is genuinely uncertain, stop that item and record the
    decision for Ainesh, unless the workstream's `scripts/` procedure has a
    Decisions section: then settle it as that section says, in every stage,
    and never wait for him. Never call AskUser.
11. **Never undo a reviewer's state.** Never dismiss an approval, re-request
    review from someone who already approved, or claim an approval is stale or
    auto-merge is armed without reading the current state.
12. **Diagnose CI from logs.** Read the failing job's log and the runner state
    before editing code or calling a failure flaky. Runner loss is not a test
    timeout; a fixture refresh changes only the intended request fields.
13. **Never defer a real issue.** "I'll open a ticket", "follow-up PR", "out of
    scope", "tracked separately", and TODO comments are not answers to a real
    problem, even one the change did not introduce. Fix it in this run's
    change, or record the specific decision only Ainesh can make (settled
    by the workstream's Decisions section instead, when rule 10 says so). Disagree
    only when the problem is not real, with evidence. Ainesh rejects
    deferral as poor taste.

## When a run opens a new PR

1. Search open and recently merged PRs touching the same files or goal, and
   read their diffs, before claiming the work is new or covered.
2. Branch fresh from the current default branch and record the base SHA;
   compare later diffs against that SHA, not a moving remote ref.
3. Inventory every consumer of the mechanism you change and migrate all of
   them together. Delete the competing path instead of keeping both.
4. Prove a bug fix red-first: the test fails before the fix and passes after.
5. Write the PR body from a cited fact sheet, then claims-check it against the
   diff. Update the body whenever a later fix invalidates a claim.
6. Mark it as workstream work: **Related Issue** carries the change link the
   run prompt supplies (`app.factory.ai/software-factory/changes/<id>`) and
   the line `Opened by Ainesh's <workstream name> workstream.` PR Shepherd
   recognizes workstream PRs by that link.
7. Open it ready for review. Reviewers are requested once the PR is finished,
   not at open: `~/.agents/skills/slack-cli/ops/review-request.md` owns the
   readiness gate and whom to ask, and PR Shepherd's review request carries it
   out for workstream PRs. Never request factory-ain3sh.

## When a run measures a target

1. Preregister the hypothesis, metric, controls, repetitions, and decision
   rule before observing results.
2. Measure the claimed target directly. Fewer characters, a passing probe, or
   one anecdote is not a latency, eval, or cost win.
3. Validate the measuring harness against current source before trusting its
   score; correct a wrong fixture openly and keep the superseded result.

## When Software Factory itself misbehaves

Report a defect when this run sees Software Factory break its own contract:
the activity coordinator, claims and requeues, state publish and memory sync,
`droid sf` commands, template Computers, generated workstream skills,
automations, or the review UI. Classify by who owns the fault, not the file
where it showed: a mistake written only in this workstream's `scripts/`,
skills, or memory is rule 8; a wrong artifact the platform generated or
transported is a defect. A bug in the target repo is the workstream's work. An
upstream outage (GitHub, Linear) or a guardrail working as designed is not a
defect, though Software Factory mishandling one can be. Under rule 13,
reporting is the required disposition for an incidental platform defect
outside this change's approved scope; do not fold its repair into an unrelated
target-repo change.

1. **Gather evidence.** Expected and observed behavior; the exact command,
   error, and output; UTC times; `droid --version`; the workstream, activity,
   change, and Computer ids. Trace the failing path at the latest dev:
   `git -C ~/repos/factory-mono fetch origin dev`, then read files with
   `git -C ~/repos/factory-mono show origin/dev:<path>` (the checkout itself
   may be behind) and cite `file:line` with the SHA. When the source is
   unreachable or the cause stays unconfirmed, report anyway and say what is
   missing; never guess a cause. Keep secrets, tokens, and customer data out.
2. **Dedupe.** Load the tools with ToolSearch
   (`select:linear__get_issues,linear__get_comments,linear__create_issue,linear__create_comment,linear__get_issue,slack__post_message,slack__get_conversation_history`).
   Read this workstream's events
   (`droid sf db-list-events --workstream <id> --limit 200`) and stage memory
   for prior defect reports, including incomplete reports. Search SOF
   titles with `linear__get_issues` (`team_key` `SOF`, no `open_only`, no
   date cutoff) using two or three distinctive terms, and read likely matches.
   A failed search is not "no match". Search once more right before filing:
   runs in other workstreams can hit the same defect at the same time.
   - Incomplete prior report: reconcile it before applying the open-match
     rule. Re-read the known issue and the channel history; perform only the
     writes confirmed missing, then verify and record (step 5). A failed or
     incomplete read does not prove absence. Never create another ticket to
     retry its announcement.
   - Open match: do not file. Comment with `linear__create_comment` only with
     evidence the ticket and its comments (`linear__get_comments`) lack, such
     as another workstream or a new failure mode; a new run id or time is not
     new evidence. No Slack post. Name the ticket in the memory entry, and
     record an event only when you commented.
   - Completed match: check whether its fix reached the failing runtime. If
     not, reuse that ticket and note the pending rollout in memory. File a
     linked recurrence only when the fix reached that runtime or new evidence
     shows the closure was wrong.
   - Canceled match: read its reason and follow any duplicate link. File only
     when the current evidence is not covered by that disposition.
3. **File.** `linear__create_issue`: team SOF
   `1d671026-0e0b-4680-9107-55d1febc18f9`, state Pod Triage
   `0686fb8e-2323-435b-8306-3f5c266fef04`, label Bug
   `8f83f0f9-b056-4143-a09d-94d55e5b4474`, subscriber Ainesh
   `e18b7267-8ef6-48ec-a07c-2e0345b5e756`, no assignee, no priority, and the
   project that owns the failing surface:

   | Surface | Project |
   |---|---|
   | Coordinator, claims, state publish, template Computers, automations (default) | Runtime Environment `a11aa65f-c948-47d6-a16d-dfa601ef710e` |
   | `droid sf db-*` commands and the signal, change, event, and memory data | Data Model `db647d59-129e-426a-928e-b0b9a8fb5bcc` |
   | Workstream creation, generated skills, loop behavior | Loop Quality `724f0680-8e2e-4a2f-b164-1d025e7e6266` |
   | Desktop or web review UI and inbox | Workstream Dashboard `9f51a9f9-d4a7-4d44-a220-13ab8cec6a8d` |
   | Access, privacy, service accounts | Ownership & Permissions `b85c5fe1-1492-4908-880d-2fc4dc2b5952` |

   The title states the observed effect. The body has Problem, Observed,
   Impact, Code path (the SHA, or "not established" with what is missing),
   Proposed direction, Acceptance criteria, and Related, then ends with
   `Reported by the <workstream name> workstream (<workstream id>) on
   Ainesh's behalf.` SOF-391 is the model.
4. **Announce.** `slack__post_message` to #product-workstreams `C0B8NS7K4V8`:
   `Filed <issue URL|SOF-N>: <the effect in one sentence>.`, then one short
   paragraph starting `<@U0AGMAQGPC2>'s <workstream name> workstream hit it`
   with what happened, any confirmed cause, and the workaround. Write as the
   Factory bot, not as Ainesh.
5. **Verify and record.** Re-read the issue with `linear__get_issue`: team,
   state, project, Bug label, no assignee, no priority (subscribers are not
   readable there; the create call's `subscriber_ids` stands). Re-read the
   message with `slack__get_conversation_history` (`oldest` and `latest` set
   to its `ts`, `inclusive` true) and confirm it holds the issue URL. Then
   record
   `droid sf db-add-event --workstream <id> --stage <stage> --severity <severity> --title "Filed SOF-N: <title>" --detail "<impact on this workstream>. <issue URL>  Reference: Slack message <ts>"`,
   with stage `intake` or `triage` for those runs, `worker` for investigate,
   implement, and steward, and `health` for health and the steward sweep;
   severity `error` when the workstream cannot make progress, `warning`
   when action is needed but other work can continue, `info` otherwise. Name
   the ticket in this run's memory entry.
6. **Carry on.** Continue the run's task by the safest path the defect leaves
   open, and say which path in the memory entry.

If a tool is unavailable, or a write fails or remains unverified after
rereading, record one warning titled
`Software Factory defect report incomplete: <title>`. Its detail holds the
draft, every confirmed issue or Slack reference, and the next unverified step;
the next run reconciles it through step 2. Never repeat a write whose outcome
remains unknown. When `droid sf` itself is broken and no event can be
recorded, put those same recovery details in the run's final message.

## Headless facts (ain3sh-dev template)

- `gh` and git act as factory-ain3sh: every push, reply, and merge appears as
  Ainesh. Load **voice** before writing anything a person reads.
- `~/repos/factory-mono` stays on `dev`. A hook denies checkout, commit, push,
  reset, rebase, and similar verbs whenever the command or cwd references that
  path. Do branch work in `~/repos/factory-mono-worktrees/<branch>`;
  `git -C ~/repos/factory-mono fetch` and `worktree add` are allowed. Never put
  a mutating git verb and a `repos/factory-mono` path in one command.
- Never install packages in a worktree. Mirror dependencies with
  `python3 ~/.agents/skills/worktree-setup/scripts/repair.py` from inside it.
  `worktree-cli` and `stack` are not installed; restack with
  `git rebase --onto` per **sync-target**.
- Skills marked `disable-model-invocation` (address-review, implement,
  post-review, explain-diff) cannot load through the Skill tool. Read
  `~/.agents/skills/<name>/SKILL.md` and its references directly.
- Laptop-only paths in `~/.agents` docs (`/home/ain3sh/...`,
  `ssh factory-dev-box`, `dsx`, `slck`) do not exist here. Skip them.

## Failure map

| Symptom | Action |
|---|---|
| A hook denies a git command | Move to the worktree and split the command. |
| The reader script exits non-zero | Stop acting on that item and report the error text. Do not guess. |
| A droid is missing or runs on the wrong model | Rerun `scripts/setup-run.sh`; if still missing, use built-in subagent types and record a warning event. |
| A write's verification fails | Re-read the target; resend only when the read proves it did not land. |
| A `droid sf` command, the coordinator, or another platform surface misbehaves | Follow *When Software Factory itself misbehaves*. |
