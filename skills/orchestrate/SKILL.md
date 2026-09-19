---
name: orchestrate
description: 'Coordinate the model-pinned droids (glm, sol, fable, astra) as Astra main session, an explicitly assigned Astra orchestrator child, or top-level Fable told "be an orchestrator". Every other child keeps its assigned role.'
user-invocable: false
---

# Orchestrate

Own the sequence and acceptance of delegated work; a successful subagent report
does not make its implementation understandable or ready to merge.

## Act

| Goal | Action |
|---|---|
| Assign or resume work | Apply [delegation](references/coordination.md#delegation); handle small changes directly or send one owner a bounded `Task` handoff. |
| Accept an implementation | Read the decisive diff and apply the [readability gate](references/readability.md) before accepting the report. |
| Understand an unexplained block | Ask its existing author for the mechanism, evidence, and clearer code or local rationale. Without an author to resume, investigate directly. |
| Reject an obscure implementation | Return the specific block and required simplification to its owner; do not pass it to the user as merge-ready. |
| Verify or ship | Use the owning workflow skills listed in [coordination](references/coordination.md#gates-stay-owned). |

## Detect

Check your seat before dispatching: Astra/GPT-6 main session, an Astra child
explicitly assigned orchestration, or top-level Fable told "be an orchestrator".
Every other child keeps its assigned role.

At every implementation handoff, ask: **Can I explain what this block does,
why it has this shape, and why the obvious simpler approach is insufficient?**
If the why is not apparent at a glance, assume a human maintainer will struggle
too and run the readability gate.

## Rules

1. Never accept obfuscated code as mergeable code, even with green tests or a
   confident author. Require simplification or verified necessity with a
   discoverable explanation; see the readability gate.
2. Never turn a small local fix into a mandatory handoff. Follow the
   [delegation boundary](references/coordination.md#delegation); substantive
   implementation still goes to a coding owner.
3. Never let parallel writers share a changing contract or write ownership.
   Settle prerequisites and approvals before dispatching consumers.
4. Never replace missing Task access with shell-spawned agents. Return a
   dispatch request to the parent.
5. Never stop with approved work silently deferred. Keep each item owned
   through completion or a concrete blocker requiring the user's decision.

## Failure map

| Symptom | Action |
|---|---|
| Code looks inexplicable; author reports success | Hold acceptance and run [readability](references/readability.md). |
| Clarification exists only in the agent transcript | Have the owner simplify the code or record the non-obvious constraint beside it. |
| Explanation sounds plausible but lacks evidence | Verify the decisive caller or external contract; do not treat the explanation as proof. |
| Model unavailable, interrupted writer, or unclear ownership | Follow [coordination](references/coordination.md) before reassigning. |
| Fresh edits invalidate QA | Re-run the affected checks under the stable-revision rules in coordination. |

## References

Load on demand; do not reabsorb into this file:

- [references/coordination.md](references/coordination.md): seats, staffing,
  handoffs, ownership, recovery, QA, and workflow gates.
- [references/readability.md](references/readability.md): comprehend, clarify,
  simplify or justify, and re-check before accepting an implementation.
