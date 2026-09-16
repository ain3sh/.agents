# Review ledger & dossier

Two paired artifacts per review worktree (worktree = one PR):

| File | Role | Write mode |
|---|---|---|
| `./.agents/review.md` | **Dossier** — compact current state: findings, tiers, statuses, coverage. What follow-up loads. | Refreshed at checkpoints; state sections replaced each pass |
| `./.agents/review.notes.md` | **Notes** — append-only event log: every candidate, kill, fold, retier, dispatch, reconciliation, with the evidence that caused it. | Appended in the same turn as the event; never edited or batched |

State lives in the dossier; history lives in the notes. The dossier answers "what do we post / what does the next pass need"; the notes answer "why is F14 a warning now" and "did we already investigate X". Killed suspicions are as valuable as findings — recorded at the moment of the kill with the killing evidence, they stop any later pass or worker from re-investigating settled ground. If the dossier is lost it is reconstructable from the notes; the reverse is false — which is why notes are written first and continuously.

Both files are untracked, never committed, and owned by the main reviewer alone — workers never touch them. `mkdir -p ./.agents` on first write.

## Notes file (`review.notes.md`)

Scaffold once, at review start (first-pass §1), before verification begins:

```markdown
# Review Notes — PR <number>

Repo: <owner>/<repo>
Started: <ISO date> @ <HEAD_SHA>

---
```

Append one block per event, **in the same turn the event happens — never batched to end-of-phase**. Context compression can strike between any two turns; an unwritten conclusion is a lost conclusion. Append-only means no anchor-matching edits into a file being restructured — a dumb write to the end, cheap enough to never skip.

```markdown
## <ISO timestamp> — <one-line title>
**Type**: candidate | confirm | kill | fold | retier | dispatch | reconcile | env | gate | post
**Refs**: <F-ids / worker sids / category>
**Context**: <2-3 lines: what raised it>
**Resolution**: <what was concluded, on what evidence; what was rejected and why>
```

Append triggers — each is a moment where unique state exists only in-context:

- **candidate** — a suspicion or finding is first articulated (including first-pass §3 suspicions not settled inline). Assign its `F<id>` here.
- **confirm / kill** — evidence settles a candidate either way; name the exact probe or invariant that did it.
- **fold** — a discovery merges into an existing finding (`fold → F12`) instead of becoming a duplicate.
- **retier** — any severity change, with the reason (new evidence, user calibration, patch-coherence clustering).
- **dispatch** — workers sent: category, session ids, modality pairing.
- **reconcile** — a worker returned: outcome per proposition, modality agreement or disagreement (a disagreement is itself the named open question). Write before processing the next return.
- **env** — environment quirk discovered (runtime version pins, filesystem constraints, hoisted binaries); later worker prompts inherit these from the dossier's env notes.
- **gate** — the architecture-gate ruling (`continue` / `revise`, reason, unreviewed areas on `revise`; a re-rule after the worker returns is a second entry), acceptance admissions and waivers (`acceptance.md`), and approval-gate outcomes: user edits, drops, re-severities, verdict choice.
- **post** — review submitted: review id, comment ids → anchors.

The notes file persists across passes append-only — follow-ups continue the same log.

## Dossier file (`review.md`)

Refreshed at checkpoints, not per event (the notes carry the loss-proof burden): after the architecture-gate ruling, after the review-state summary, at each category close, at the approval gate, and after posting — `/post-review` owns the final write of a pass. Replace state sections each pass; append one history line.

Findings carry **stable IDs** (`F1, F2, …`, assigned at candidate time, never renumbered or reused) and a **status**: `candidate | confirmed | killed | folded→Fn | posted`. Notes entries reference these IDs; tier changes appear in the notes as `retier` entries, the dossier shows only the current tier.

On load (routing/follow-up): verify the dossier's PR number matches the target — mismatch (e.g. run from a shared worktree) → treat as no dossier. Worktree deleted → both files gone; that's fine — the GitHub review thread is the durable fallback, and follow-up reconstructs the minimum from it.

### Schema

```markdown
# PR <number> — <title>

repo: <owner>/<repo>
reviewed_head: <SHA>
body_seen: <fingerprint of the raw body (e.g. sha256 of `gh pr view --json body`) + last-edit timestamp>
base: <base ref> @ <merge-base SHA>
mode: <first-pass | first-pass+deeper | follow-up>
verdict: <APPROVE | COMMENT | not yet issued>
date: <ISO date>

## Root-cause / invariant model
<2-6 lines: the required behavior and hard constraints, the layer each invariant lives in,
the admitted gate report (`architecture-gate.md` "Gate report": case, owner and consumers, rows; split-only dispatch predicate, remaining range, paired loci),
the simplest viable shape you formed, and whether the review confirmed the PR's model.>

## Architecture gate
decision: <continue | revise>
reason: <one line: why the shape stands, or the structural defect and the direction>
unreviewed: <areas skipped on revise; "none" on continue>

## Description audit
<claims: verified / false / stale / unverifiable / not checked, with F-ids; required material missing>
evidence: <per cited artifact: identity (URL/attachment), access state when observed, commit anchor — one line each>
audited_body: <body_seen value this audit covers>

## Acceptance
- <scenario — surface/platform/mode>: <state, acceptance.md §4 vocabulary verbatim; failed → observation + attribution (F<id> once attributed to the PR | pre-existing → out-of-scope route | unsettled); blocked → blocker + next decision; waived → unverified limit; n/a → source reason>; evidence <probe | integration | end-to-end workflow>, <artifact ref, contents inspected>, target <revision/build as established from the evidence>

## Findings
- F<id> <status> <severity> <file:line> — <claim> — <evidence, one line> — thread: <comment id, once posted>

## Verified safe
- <suspicion> — killed by <invariant | probe result>, <one-line evidence>

## Coverage map
- <surface>: <main | static worker | probe worker | acceptance worker> at <source inspection | probe | integration | end-to-end workflow> — <outcome>
- <surface>: not deeply covered — risk <low | medium | high>

## Unresolved
- <question left open, if any>

## Env notes
- <quirks workers must inherit: version pins, filesystem constraints, tool paths>

## Worker log
- <category>: <static sid?, heavy sid?> — <conclusion, incl. cancellations and why>

## History
- <date> first-pass @ <SHA>: <verdict>, gate <continue | revise>, acceptance <passed x/y; other states listed>, <n> findings
- <date> follow-up @ <SHA>: <verdict>, <resolved x/y, new z>
```

Keep the dossier under ~100 lines: one-line evidence with pointers (thread ids, worker session ids, notes timestamps) — transcripts and reasoning chains live in the notes. Empty section → keep the header with "none"; follow-up relies on the distinction between "none" and "not recorded".
