---
name: harness-optimization
description: Optimize agent-harness reliability by tracing instructions, model choices, hooks, executor semantics, process ownership, output capture, and operator feedback to the first control-plane failure. Use when agents repeat tool misuse despite guidance, hooks teach bad retries, background or cancellation behavior corrupts evidence, or a harness fix risks becoming case-based.
---

# Harness Optimization

Treat the agent harness as a control plane: a model choice is locally rational
until the loaded policy, available affordances, and runtime semantics prove
otherwise. Optimization means removing representable failure states, not
micro-tuning latency or token usage.

First question: **did the agent disobey, or did the harness make the bad choice
locally correct?**

## Act

| Goal | Action |
|---|---|
| Preserve the incident | Stop retries. Save the transcript, exact tool input/output, hook decisions, full logs, cancellation state, and process IDs. |
| Establish the intended contract | State one invariant covering observation, ownership, completion, and failure reporting. |
| Trace the control plane | Walk instruction → model choice → hook rewrite/decision → executor → child process → output surface → operator response. |
| Classify the first break | Name it as policy-induced behavior, enforcement gap, runtime drift, executor mismatch, observability distortion, split ownership, or recovery-loop amplification. |
| Fix the owning layer | Remove the bad affordance, give one primitive the full lifecycle, and make policy plus enforcement teach that same grammar. |
| Prove the fix | Replay the incident and the lifecycle matrix in `references/procedure.md`. |

## Detect

Load this skill when any of these are true:

- an agent repeats a workflow mistake after being corrected
- a skill says one thing while hooks or tools permit or suggest another
- backgrounding, polling, filtering, retries, compaction, or cancellation
  changes the apparent result
- a hook blocks an action but emits an unusable or self-contradictory retry
- the visible failure is downstream of process, cache, registration, or output
  ownership
- the proposed fix is growing regex branches, shell parsing, reminders, or
  exception tables

Use **root-cause-analysis** for the first unintended effect, **step-through**
for temporal state, and **single-canon** when replacing the broken contract.
Do not use this skill for ordinary application bugs, isolated user error, or
generic model latency/cost tuning.

## Rules

1. Never blame the model before comparing its exact choice with every loaded
   instruction, hook affordance, and executor behavior.
2. Never fix the final error first. Find the earliest point where the harness
   made the bad path valid, attractive, invisible, or hard to recover from.
3. Never split lifecycle ownership. One primitive owns setup, execution,
   observation, persistence, cancellation, cleanup, and exit status.
4. Never teach shell choreography when an argv protocol or typed tool can
   remove the states entirely.
5. Never repair arbitrary commands with case-based parsing. Accept one tiny
   grammar; reject known violations and fail open on uncertainty.
6. Never call an interrupted run a test failure, or a stored log complete
   evidence unless live observation and process termination are also proven.
7. Never accept unit-only proof. Exercise the registered hook and real
   executor through the lifecycle matrix.

## Failure map

| Symptom | First question | Correct direction |
|---|---|---|
| Agent repeats a forbidden command | Did policy examples still recommend or normalize it? | Fix policy and affordance before adding punishment. |
| Hook blocks but retries stay wrong | Is the hook reconstructing arbitrary shell? | Emit one canonical grammar, not a rewritten command. |
| Agent sleeps or polls logs | Who owns foreground completion and observation? | One attached runner owns both live output and persistence. |
| Cancellation creates false failures | Did cancellation reach the whole child process group? | Forward, escalate, reap, and classify as interrupted. |
| Cache sentinel exists but runtime is broken | Does the sentinel prove every required artifact? | Make creation transactional and validate the completeness invariant. |
| Interactive works but automation dies | Do hook semantics differ by execution mode? | Test and document each mode explicitly. |
| Source is fixed but behavior is unchanged | Is the active runtime registration/config still stale? | Verify live wiring and delete the competing owner. |
| Fix accumulates special cases | Is the accepted language wider than required? | Shrink to one protocol and delete competing mechanisms. |

## References

- Load on demand; do not reabsorb into this file:
  `references/procedure.md` — evidence packet, actor-state trace, fix hierarchy,
  lifecycle verification matrix, stop conditions, and report schema.
