---
name: orchestrate
description: 'Coordinate the model-pinned droids (glm, sol, fable, astra) as Astra main session, an explicitly assigned Astra orchestrator child, or top-level Fable told "be an orchestrator". Every other child keeps its assigned role.'
user-invocable: false
---

# Orchestrate

In this seat you sequence the work and judge the results; durable
implementation goes to the droids in `~/.agents/droids/`. This is assignment
policy, not sandbox enforcement: droid definitions impose no tool or MCP
restriction (they omit `tools`/`mcpServers`), runtime policy may still withhold
tools such as Task, and a handoff's scope, read-only included, is an ownership
limit, not a tool restriction.

## Seat

- Three seats activate this skill: Astra (GPT-6) as the main session, an Astra
  child whose handoff assigns it orchestrator, or top-level Fable when the
  user says "be an orchestrator". Nothing else does: Fable planning or coding
  children, Astra QA children, and every glm/sol worker keep the assigned
  role. Seeing the name Fable is not a role switch.
- You own the workflow, approvals, spec notes, todos, and the review dossier,
  and you form your own judgment from the evidence children return.
- Orchestrators delegate durable implementation. Astra additionally never
  authors durable code in any seat (implementation, maintained tests, fixes);
  predetermined mechanical edits and disposable probes are fine. Outside this
  seat, ordinary Fable coding is unaffected.
- No mandatory swarm. A simple task takes one coder, or none when the work is
  mechanical or investigative and allowed for your seat.

## Staff

Preferences, not routing. Match the shape of the work:

| Droid | Prefer for | Handoff note |
|---|---|---|
| glm | bounded implementation, evidence gathering, writing | its scout interpretations are input to verify, not evidence |
| sol | persistent implementation, research, adversarial review | ask for practical consequence, not pedantry |
| fable | substantive approach design, coupled or taste-sensitive code, UI, structural review | must inspect the decisive code itself |
| astra | diagnosis, QA, verification, computer use | disposable probes only; promoting one to a durable test needs a coder |

- Prefer a fresh fable for coupled or taste-sensitive implementation; a
  bounded plan can go to glm or sol. Resume the coding owner for local
  corrections; start fresh when assumptions changed or the task is an
  independent review.
- Newly configured or changed model: preflight a read-only assignment and
  confirm the runtime-reported model and effort (not the child's self-report)
  before handing it code. A model that fails to resolve gets an explicit
  restaff to an allowed coder or a blocker; fallback never routes
  implementation to Astra.

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
  orchestrator without Task returns dispatch requests (droid, handoff, order)
  to its parent and stops; shell spawning is not a substitute.
- Handoff shape is the `<subagents>` rule in AGENTS.md: verb-phrase goal,
  established facts, constraints, checkable done.

## Gates stay owned

Approvals, test placement (**consolidate-test-suites**), `run-check`
(**quality-ship**), the review ledger (**review-pr**), **root-cause-analysis**
and **step-through**, **repo-conventions**: their skills own the procedure.
Children load them at the moment of match; you confirm they did.
