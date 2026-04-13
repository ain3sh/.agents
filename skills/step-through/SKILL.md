---
name: step-through
description: Step through a system's execution with explicit state at each transition. Use when debugging races, state machines, async bugs, regressions; stress-testing a fix; scoping features on existing state; or approaching unfamiliar code. Triggers on multi-actor sequencing, background refreshes, recovery paths, queues, "why is this broken", "walk through the flow", "this used to work", "what happens when", or "stress test this plan". Also loaded by /implement during bug-fix flows.
---

# Step-Through

Before electronic computers, "computer" was a job: a person who executed a procedure by hand, step by step, writing each intermediate value down. When a system's behavior depends on state evolving over time across multiple actors, reasoning abstractly is the wrong tool. The fix is to become the human computer: execute the system manually, step by step, writing down concrete state at every transition.

This is slower than "reviewing the logic" but catches bugs that review never will, because the act of maintaining state across steps forces contradictions to surface.

## When to use

- A bug was fixed once and regressed. The mental model used for the first fix is wrong or incomplete.
- Debugging anything involving client/server sequencing, async callbacks, background refreshes, recovery paths, queues, retries, or two actors evolving state together.
- The user proposes a fix for a state or race bug and asks you to stress-test it or think through edge cases.
- Scoping a new feature on top of an existing state model and you don't yet know where it fits.
- Approaching an unfamiliar task and you're tempted to jump straight to code.

Don't use for:
- Pure transformations with no state (renames, type fixes, formatting, config edits).
- Tasks where the failure is obvious from a single stack trace or error message.
- Well-understood changes where you already know what to write.

## The three shapes

Pick one before you begin:

| Situation | Shape |
|---|---|
| No code yet, unfamiliar task | **1. New work** |
| Code exists, bug reproduces | **2. Debugging** |
| Code exists, feature is new | **3. Scoping** |

### Shape 1: New work (build intuition first)

You have a task but no code and no plan.

1. Execute the task manually, as the human computer. If it's a scrape, poke around the site and look at real responses. If it's a pipeline, run each stage by hand. If it's an unfamiliar API, call it live.
2. At each step, write down what you actually observed, what surprised you, and what you'd have gotten wrong if you'd guessed.
3. Only after the manual execution succeeds distill the trace into code.

Done when **you stop being surprised**.

### Shape 2: Debugging an existing system

Code exists, the bug reproduces, and you probably already have a theory -- resist it.

1. **Step through the broken flow first.** Walk through the current broken behavior. At every step, write each actor's state as a named object (`client = {...}`, `worker = {...}`, `parser = {...}`). Take each actor's perspective in turn. Continue until an invariant breaks. That is the bug.
2. **Then propose a fix.**
3. **Then step through the fixed flow.** Re-run the same trace with the fix applied. Check the invariant at every step, across every phase -- not just the one that was failing.
4. **Only then write the code.**

The trap is skipping step 1 and jumping to "let me walk through the fix." That reduces the technique to "validate my theory," which entrenches wrong mental models.

### Shape 3: Scoping a new feature

1. Step through the new user flow end-to-end against the current state machine. Don't design yet; just walk it.
2. Every time you have to invent new state, bend an existing field, or hand-wave a transition, write it down. Those are your design decisions.
3. Draft the architecture from that list, not before it.

Done when **you can walk the new flow end-to-end without inventing anything mid-step**.

## How to compute well

**Keep state explicit at every step.** At every transition, write each actor's state as a named object. The act of writing forces concreteness.

**Switch perspectives deliberately.** Most race bugs live in the seam between two actors. Walk the flow once as each actor in turn.

**Stay in one head.** Do not fan the walk out to sub-agents. Hand-computing a state machine is cheap because one head holds all the state and notices the contradiction mid-step.

**Pick the right level of abstraction.** A bug in how two React state updates interleave won't show up if you're tracing HTTP requests. Figure out where the contention likely lives, then compute at that level.

**Ground transitions in actual code.** When in doubt about what a function does at a given step, open the file and re-read it. Don't compute what you think the function does; compute what it actually does.

## Failure modes

| Failure | What it looks like | Fix |
|---|---|---|
| Narrative computation | Prose sequences without explicit state | Write `state = {...}` at every step |
| Skipping the broken flow | Jumping straight to the fix | Back up, compute the broken behavior first |
| Sub-agent fanout | Parceling the walk across parallel agents | Context-gather with agents, walk in one head |
| Stopping at the failing phase | Walking only the broken phase | Walk every phase end-to-end with the fix |
| Wrong abstraction level | Tracing HTTP when the bug is in render order | Locate the bug's likely home, compute at that level |
| Wishful code-reading | Describing what the function "should" do | Re-read the actual source at every transition |

## Checklist

Before declaring the walk complete:

- [ ] I wrote each actor's state as a named object at every step
- [ ] I took the perspective of each actor at least once
- [ ] I walked in one head (no sub-agent fanout)
- [ ] (Debugging) I stepped through the broken flow before walking the fix
- [ ] (Debugging) I walked every phase with the fix applied, not just the failing one
- [ ] When I hit a contradiction, I stopped and explained it
- [ ] I grounded uncertain transitions by re-reading actual source
- [ ] (New work) I observed real input/output, not imagined shapes
- [ ] (Scoping) Every invented state or open question is written down
