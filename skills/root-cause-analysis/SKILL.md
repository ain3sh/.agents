---
name: root-cause-analysis
description: Root-cause-first debugging by tracing expected behavior to the first unintended side effect before changing contracts, parsing, or types. Use when debugging protocol errors, deserialization failures, null payloads, missing fields, restore or hydration issues, state-ownership bugs, unexpected requests, background mutations, or reviewing code where the visible failure may be downstream noise. Also loaded by /implement during bug-fix flows.
---

# Root-Cause Analysis

Golden path: **repro → invariant → narrow until the region fits in one head → read → prove**. When prove fails, narrow again from the new boundary. Nothing is a root cause until prove passes.

## Core instruction

Before fixing the error, prove whether the code path that produced it was intended.

Do not stop at the first contract, parsing, type, null, or schema error. Treat it as a possible symptom.

## Inputs (pull before reasoning)

RCA without the failure state is guesswork. Before stating expected behavior, pull every referenced artifact via project-local skills or MCP tools:

- Bug reports, error logs, stack traces, trace IDs, core dumps
- Sentry / Rollbar / DataDog / Axiom / CloudWatch payloads
- Repro scripts, HAR files, screen recordings, session captures

Read-only fetches don't violate spec mode -- skipping artifacts sabotages the RCA.

The repro is the oracle for the whole RCA: narrowing splits on it, and the final hypothesis is proven against it. Make it deterministic and cheap to run before reasoning. A repro that flakes or takes minutes gets run too rarely to catch a wrong hypothesis.

If you cannot reproduce the failure or read its artifacts, **stop and surface the gap** rather than guessing. A guess phrased as a root cause is worse than "I don't have enough state to RCA this yet."

## Two moves

RCA alternates two moves. Neither is a fallback for the other; the region's size picks the move.

- **Narrow**: shrink the region that can contain the cause by running experiments whose outcome you cannot predict (bisection over history, input, layer, writers, environment, state). Answers *where*. Splits on the repro as oracle.
- **Read**: trace the causal chain inside a region small enough to hold in one head. Answers *whether the write was intended* and names the first unintended side effect.

## Workflow (in order)

1. State the expected behavior in plain language: what user action or system event was supposed to happen?
2. State the invariant in one sentence.
3. State what definitely did not happen.
4. **Pick the opening move.** Open with **narrow** if any narrow row fires; otherwise **read**.

   | Signal | Open with |
   |---|---|
   | A known-good reference exists: it worked at commit/version X, in env A, with input Y, with flag off | Narrow over that delta |
   | You cannot name the candidate call path in one sentence | Narrow |
   | The error surfaces far from anywhere it could originate (edge deserialization, generic null, unexpected request) | Narrow by asserting the invariant at layer boundaries |
   | You can name the path in one sentence and hold it in one head (~3 hops) | Read |

5. **Narrow** until the region is one unit you can read whole (one commit diff, one function, one writer, one field). Loop, axes, and oracle rules: `references/bisect.md`. Write the boundary (`good: … / bad: …`) after every experiment.
6. **Read**: trace the causal chain. What exact call path led from the intended action or system event to the observed effect?
7. Ask whether the request, mutation, or side effect should have happened at all under the expected behavior and invariants.
8. Identify who owns the state at each layer: the canonical source of truth and every competing source (observer-driven syncing, lifecycle startup code, persistence restore, retry logic, background work).
9. Find the first unintended side effect or write. This is a hypothesis.
10. **Prove it against the repro.** Write the prediction your hypothesis makes and nothing else would: with the cause toggled off (commit reverted, writer disabled, write guarded) the oracle passes; toggled back on, it fails; and the invariant breaks at exactly the line you named. Run it. A failed prediction means the hypothesis is wrong: record the new `good`/`bad` boundary and return to step 5. Two live hypotheses need one experiment whose outcome differs between them, not two experiments in turn.
11. Only then decide whether a downstream contract fix is still necessary: is the contract wrong, or did unintended logic reach the contract?

When the proven causal chain spans more than two actors or transitions, load
`show-me` after step 11 and replace the prose chain with one grounded causal flow
or sequence. Mark the first unintended edge; do not visualize a theory.

## Switch to narrow when reading becomes guessing

Check these while reading. Any one firing means the region is bigger than one head: stop, write the current `good`/`bad` boundary, and pick a split axis from `references/bisect.md`. Do not wait to be told.

- Two hypotheses formed and dropped, and no experiment eliminated either.
- A fourth file opened without the candidate region shrinking.
- Re-reading a file you already read.
- About to apply a fix "to see if the symptom goes away."
- Writing "maybe", "perhaps", or "let me try" about the cause.

## Rules

- Do not make the contract more permissive unless you can prove the observed payload is intended in the final design.
- Prefer fixing the upstream logic bug over accepting bad downstream data.
- Separate symptom, trigger, root cause, minimal safe fix, and architectural follow-up.
- If a low-level fix is still needed, explain why the upstream fix is not sufficient or why both are required.
- Identify the correct layer to fix first.
- Name the first visible wrong behavior, not only the final error.
- Never report a narrowing result as a root cause. "Commit X broke it" or "hook Y writes it" is a location and a trigger; read that region to name the first unintended write and why it was unintended.
- Never narrow with a flaky oracle -- bisection converges on noise.
- A root cause is a hypothesis until the repro confirms its prediction. Applying a fix before naming a mechanism is guess-and-check; toggling a named cause to test its prediction is verification. Expect to iterate; a failed prediction is a new boundary, not a dead end.

## Hidden write checks

Treat non-explicit writes as suspicious by default.

- Audit lifecycle hooks, callbacks, subscribers, watchers, interceptors, middleware, retries, background jobs, cache refreshers, persistence restore, scheduled tasks, and startup code.
- Check whether derived data is being mirrored into another store, cache, file, queue, session, or database through an observer or helper layer.
- Prefer explicit command handlers, request handlers, job runners, or user actions as writers; treat startup-time and background writes as suspects until proven intentional.
- If a framework has automatic reactivity or lifecycle execution, map this rule onto its equivalent constructs without assuming the framework behavior is correct.
- When the suspect list is longer than one head holds, narrow over it: disable or stub half the writers and re-run the oracle (`references/bisect.md`, writers axis).

## Output format

- Expected behavior
- Invariant
- What definitely did not happen
- Bug class
- Narrowing record (when narrowed): axes used, final `good`/`bad` boundary
- Causal chain from intended action to system effect
- First unintended side effect
- Canonical source of truth
- Competing sources of truth
- Symptom
- Trigger
- Root cause
- Repro verification: prediction, toggle run, oracle result
- Correct layer to fix first
- Minimal safe fix
- Architectural follow-up
- Proposed patch

Keep the output textual when the chain is simple. When `show-me` fires, its
representation occupies **Causal chain from intended action to system effect**;
do not repeat the same chain in prose.

## References

Load on demand; do not reabsorb into this file.

- `references/bisect.md` -- the narrowing loop: split axes with commands, oracle requirements, stopping condition, pitfalls.
