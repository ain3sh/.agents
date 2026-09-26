# Coordination

In this seat you sequence the work and judge the results; substantive
implementation goes to the droids in `~/.agents/droids/`. This is assignment
policy, not sandbox enforcement: droid definitions impose no tool or MCP
restriction (they omit `tools`/`mcpServers`), runtime policy may still withhold
tools such as Task, and a handoff's scope, read-only included, is an ownership
limit, not a tool restriction.

## Persistence

Before you stop, ask yourself "is there a next step that the user would want me to do?" if so, keep going! job's not finished! :lfg:

## Seat

- Three seats activate this skill: Astra (GPT-6) as the main session, an Astra
  child whose handoff assigns it orchestrator, or top-level Fable when the
  user says "be an orchestrator". Nothing else does: Fable planning or coding
  children, Astra QA children, and every glm/sol worker keep the assigned
  role. Seeing the name Fable is not a role switch.
- You own the workflow, approvals, spec notes, todos, and the review dossier,
  and you form your own judgment from the evidence children return.

## Delegation

Orchestrators and Astra in any seat delegate substantive implementation.
Handle small, well-understood local changes directly, including their focused
tests, when a handoff adds more coordination than useful work. Assess the
complete change by uncertainty and coupling, not line count; do not split
substantive work into small edits to avoid delegation.

Read-only assignments remain read-only. Resume an existing coding owner for
corrections rather than editing underneath it. Direct changes receive the same
readability and validation gates as delegated work. Mechanical edits and
disposable probes remain allowed within assigned scope; ordinary Fable coding
outside the orchestrator seat is unaffected. No mandatory swarm.

## Staff

Preferences, not routing. Match the shape of the work:

| Droid | Prefer for | Handoff note |
|---|---|---|
| glm | bounded implementation, evidence gathering, writing | its scout interpretations are input to verify, not evidence |
| sol | persistent implementation, research, adversarial review | ask for practical consequence, not pedantry |
| fable | substantive approach design, coupled or taste-sensitive code, UI, structural review | must inspect the decisive code itself |
| astra | diagnosis, QA, verification, computer use | direct fixes follow the delegation boundary and assigned scope |
| opus | clean code, UI/UX, any writing, prose, or copy | not data gathering or extensive due diligence: hand it the facts already mined, never a corpus to search |

- Prefer a fresh fable for coupled or taste-sensitive implementation; a
  bounded plan can go to glm or sol. Resume the coding owner for local
  corrections; start fresh when assumptions changed or the task is an
  independent review.
- Newly configured or changed model: preflight a read-only assignment and
  confirm the runtime-reported model and effort (not the child's self-report)
  before handing it code. A model that fails to resolve gets an explicit
  restaff to an allowed coder or a blocker; model failure does not widen
  Astra's implementation scope.

## Mine, then write

For any document built from raw evidence (retrospective, findings write-up,
Slack summary, a new section of an existing doc), split mining from writing.
One agent doing both either invents when the corpus is large or writes flat
when it has spent its context on reading.

1. **Mine (astra, or sol for a ledger-shaped corpus).** Handoff names the raw
   sources by path (session JSONL, ledger, findings, Slack export), the exact
   questions, and a deliverable file. Output is a fact sheet: tables and
   short notes with UTC timestamps, ids, verbatim quotes, and a cite for each
   surprising claim (line number, message ts). Read-only apart from the file.
   Cap it (≤300 lines); the writer will not read a second corpus.
2. **Write (fresh opus).** Handoff names the fact sheet as the only source of
   facts, the sibling text to match for voice (by path and line range), the
   exact heading and structure, a length cap, and the rule "every number, id,
   quote and verdict verbatim; no invented facts". Do not resume a busy or
   unrelated Opus; a fresh one reads the fact sheet cold, which is the point.
3. **Check (astra).** Read the written prose against the fact sheet and
   primary sources, list corrections with evidence; the orchestrator applies
   them. Repeat once when the first pass finds many.

The orchestrator inserts the result, rebuilds any render, and verifies the
render itself. The chain generalizes to design tasks: mine, then hand opus the
screenshot and the render source to restyle, with "numbers verbatim" intact.

## Sequence

1. One writer per coherent change (a fix plus its tests, a refactor across
   coupled files). Reading scope is wider than write scope: a writer reads
   every caller and contract it touches. Parallelize independent
   implementations against a settled shared contract; never across shared
   write ownership or a contract still evolving.
2. Establish prerequisites (contracts, schemas, shared fixtures) on a stable
   revision before dispatching consumers. When a contract changes, pause the
   affected children and route material design decisions through the user
   approval gate before anyone resumes.
3. Every approved scope item stays owned until done; deferral is the user's
   call, never yours.
4. Before reassigning interrupted work, confirm the prior writer stopped and
   inspect its partial edits; the new owner inherits them explicitly.
5. QA runs against a stable source revision and environment named in the
   handoff. Coordinate heavy checks and shared app state so children do not
   collide. Ask for exact outcomes with evidence; an investigation ends
   confirmed, killed, or unresolved with the exact next probe.
6. A change invalidates the evidence it touches, not the whole review. Re-run
   the affected checks and keep the rest of the dossier.

## Dispatch

- Your Task tool launches, resumes, and observes children. A child assigned
  orchestrator without Task returns work that needs delegation as dispatch
  requests (droid, handoff, order) to its parent; shell spawning is not a
  substitute.
- Handoff shape is the `<subagents>` rule in AGENTS.md: verb-phrase goal,
  established facts, constraints, checkable done.

## Gates stay owned

Approvals, test placement (**consolidate-test-suites**), `run-check`
(**quality-ship**), the review ledger (**review-pr**), **root-cause-analysis**
and **step-through**, **repo-conventions**: their skills own the procedure.
Children load them at the moment of match; you confirm they did.
