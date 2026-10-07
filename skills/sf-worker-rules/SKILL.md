---
name: sf-worker-rules
description: Operating rules for headless Software Factory workstream runs on Ainesh's behalf (intake, triage, investigate, implement, steward, steward sweep, health). Use at the start of every such run, before reading sources or changing anything.
---

# Software Factory Worker Rules

No human is present. These rules stand in for the judgment Ainesh would apply
mid-run. The workstream's own skill owns its procedure; this skill owns how
every procedure is carried out. When they conflict, the workstream skill wins
on *what* to do and these rules win on *how carefully*.

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
    decision for Ainesh. Never call AskUser.
11. **Never undo a reviewer's state.** Never dismiss an approval, re-request
    review from someone who already approved, or claim an approval is stale or
    auto-merge is armed without reading the current state.
12. **Diagnose CI from logs.** Read the failing job's log and the runner state
    before editing code or calling a failure flaky. Runner loss is not a test
    timeout; a fixture refresh changes only the intended request fields.

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

## When a run measures a target

1. Preregister the hypothesis, metric, controls, repetitions, and decision
   rule before observing results.
2. Measure the claimed target directly. Fewer characters, a passing probe, or
   one anecdote is not a latency, eval, or cost win.
3. Validate the measuring harness against current source before trusting its
   score; correct a wrong fixture openly and keep the superseded result.

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
