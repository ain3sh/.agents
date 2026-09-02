---
name: root-cause-analysis
description: Root-cause-first debugging by tracing expected behavior to the first unintended side effect before changing contracts, parsing, or types. Use when debugging protocol errors, deserialization failures, null payloads, missing fields, restore or hydration issues, state-ownership bugs, unexpected requests, background mutations, or reviewing code where the visible failure may be downstream noise. Also loaded by /implement during bug-fix flows.
---

# Root-Cause Analysis

## Core instruction

Before fixing the error, prove whether the code path that produced it was intended.

Do not stop at the first contract, parsing, type, null, or schema error. Treat it as a possible symptom.

## Inputs (pull before reasoning)

RCA without the failure state is guesswork. Before stating expected behavior, pull every referenced artifact via project-local skills or MCP tools:

- Bug reports, error logs, stack traces, trace IDs, core dumps
- Sentry / Rollbar / DataDog / Axiom / CloudWatch payloads
- Repro scripts, HAR files, screen recordings, session captures

Read-only fetches don't violate spec mode -- skipping artifacts sabotages the RCA.

If you cannot reproduce the failure or read its artifacts, **stop and surface the gap** rather than guessing. A guess phrased as a root cause is worse than "I don't have enough state to RCA this yet."

## Workflow (in order)

1. State the expected behavior in plain language: what user action or system event was supposed to happen?
2. State the invariant in one sentence.
3. State what definitely did not happen.
4. Trace the causal chain: what exact call path led from the intended action or system event to the observed effect?
5. Ask whether the request, mutation, or side effect should have happened at all under the expected behavior and invariants.
6. Identify who owns the state at each layer: the canonical source of truth and every competing source (observer-driven syncing, lifecycle startup code, persistence restore, retry logic, background work).
7. Find the first unintended side effect or write.
8. Only then decide whether a downstream contract fix is still necessary: is the contract wrong, or did unintended logic reach the contract?

When the proven causal chain spans more than two actors or transitions, load
`show-me` after step 8 and replace the prose chain with one grounded causal flow
or sequence. Mark the first unintended edge; do not visualize a theory.

## Rules

- Do not make the contract more permissive unless you can prove the observed payload is intended in the final design.
- Prefer fixing the upstream logic bug over accepting bad downstream data.
- Separate symptom, trigger, root cause, minimal safe fix, and architectural follow-up.
- If a low-level fix is still needed, explain why the upstream fix is not sufficient or why both are required.
- Identify the correct layer to fix first.
- Name the first visible wrong behavior, not only the final error.

## Hidden write checks

Treat non-explicit writes as suspicious by default.

- Audit lifecycle hooks, callbacks, subscribers, watchers, interceptors, middleware, retries, background jobs, cache refreshers, persistence restore, scheduled tasks, and startup code.
- Check whether derived data is being mirrored into another store, cache, file, queue, session, or database through an observer or helper layer.
- Prefer explicit command handlers, request handlers, job runners, or user actions as writers; treat startup-time and background writes as suspects until proven intentional.
- If a framework has automatic reactivity or lifecycle execution, map this rule onto its equivalent constructs without assuming the framework behavior is correct.

## Output format

- Expected behavior
- Invariant
- What definitely did not happen
- Bug class
- Causal chain from intended action to system effect
- First unintended side effect
- Canonical source of truth
- Competing sources of truth
- Symptom
- Trigger
- Root cause
- Correct layer to fix first
- Minimal safe fix
- Architectural follow-up
- Proposed patch

Keep the output textual when the chain is simple. When `show-me` fires, its
representation occupies **Causal chain from intended action to system effect**;
do not repeat the same chain in prose.
