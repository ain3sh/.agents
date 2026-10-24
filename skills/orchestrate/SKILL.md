---
name: orchestrate
description: "Load once user-given objective received, and for refreshers before subagent delegations."
---

# Orchestrate

Own the sequence and acceptance of delegated work. You are on the hook for what
children produce: a successful report does not make an implementation
understandable or ready to merge.

## Models

### Opus

- Default for a lot of things
- Extremely intelligent and versatile
- Great for system design and clean code implementation
- Great for writing and prose
- Tendency to be lazy/underdiscover/guess-from-memory unless prodded and steered to stay sharp; scoping helps with this
- Overprescribing can hurt its creativity and taste, so prompting to exceed expectations, etc. can work quite well

### Astra

- Best in the world at live QA, computer use, etc.
- Extremely thorough at mining information / swaths of data sources
- Great at adversarial testing, attacking code, and rigorous reviews
- Terrible at designing UI/UX but great at probing
- Very intelligent, but jagged behaviour

### Fable

- Very intelligent and "big model smell"
- Strong system design and experiment/research hillclimbing director
- Can be excellently creative when prompted correctly
- Stays grounded and excellent at long-term coherence
- Can be slow, and lack "drive"

### DS-Flash

- Very lean, fast firecracker
- Good attacker
- Quite intelligent, but high variance / low pass@1; can compensate with overcoverage

## Prompting

- Provide verified, ground-truth context/facts, useful commands, etc., that you don't want it to rediscover.
- Provide prime-directive, action-oriented *goals*, not a prescription on how.
- Provide hard constraints when you deem apt.
- Provide a checkable definition of done.
- Suggest or directly trigger skills freely.

## Rules

1. Never accept obfuscated code as mergeable code, even with green tests or a
   confident author. Require simplification or verified necessity with a
   discoverable explanation; see the readability gate.
2. Never let parallel writers share a changing contract or write ownership.
   Settle prerequisites and approvals before dispatching consumers.
3. Never replace missing Task access with shell-spawned agents. Return a
   dispatch request to the parent.
4. Never accept a child's report unread. Read the decisive diff and run the
   [readability gate](references/readability.md) first.

## Failure map

| Symptom | Action |
|---|---|
| Code looks inexplicable; author reports success | Hold acceptance and run [readability](references/readability.md). |
| Clarification exists only in the agent transcript | Have the owner simplify the code or record the non-obvious constraint beside it. |
| Explanation sounds plausible but lacks evidence | Verify the decisive caller or external contract; do not treat the explanation as proof. |
| Child rediscovered what you already knew, or returned narrative instead of evidence | The brief was missing facts or a checkable done ([prompting](#prompting)); fix it before resuming. |
| Model unavailable, interrupted writer, or unclear ownership | Follow [coordination](references/coordination.md) before reassigning. |
| Fresh edits invalidate QA | Re-run the checks those edits touch; keep the rest of the evidence. |

## References

- [references/coordination.md](references/coordination.md): delegation and
  the fan-out workflows (mine then write; design, build, attack).
- [references/readability.md](references/readability.md): comprehend, clarify,
  simplify or justify, and re-check before accepting an implementation.
