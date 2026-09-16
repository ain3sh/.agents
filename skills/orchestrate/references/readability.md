# Readability Is an Acceptance Gate

Obfuscated code is not mergeable code. The orchestrator must understand the
implementation rather than forward its author's confidence to the user.

## Inspect before accepting

Read the decisive changed blocks and their immediate context. Explain each
block's effect, owning abstraction, and reason for its shape in plain language.
If the why is not apparent at a glance, treat that friction as evidence that a
human maintainer will struggle too. Pause acceptance.

This is a trigger to investigate, not proof that unfamiliar domain logic is
wrong. Non-obvious external contracts, security ordering, and measured
performance constraints may justify an unusual shape. Trace the relevant
caller, dependency API, or experiment before deciding.

## Clarify or reject

1. **Ask the existing author first when the reason is unclear.** Resume its
   subagent with the exact block and missing explanation:

   > What constraint requires this shape? Show the decisive source or repro,
   > explain why the simpler existing primitive cannot do it, and return the
   > smallest clearer implementation or local rationale.

   If no author is available, investigate directly within your role. Do not
   spawn a reviewer for a question answerable with a few reads.
2. **Reject plainly poor structure without a ceremonial clarification round.**
   Name the indirection, misleading name, overlapping mechanism, or hidden
   ordering assumption. Ask the owner to simplify it; use **structural-review**
   and **single-canon** when they match.
3. **Verify the answer.** A convincing narrative is not evidence. Check the
   cited contract or behavior and whether a supported dependency API or release
   already removes the awkwardness. Do not invent an adapter just to conceal a
   required upstream name.
4. **Make the explanation survive the session.** Prefer clearer names, flow,
   and reuse. When the unusual shape is necessary, add a succinct comment
   beside it naming the constraint and why the tempting alternative fails,
   with a source/version anchor when useful. A transcript-only explanation
   leaves the next maintainer with the same problem.
5. **Re-read the result without the author's narrative.** Can a maintainer
   reconstruct the intent from the code and its local explanation? Re-run any
   checks invalidated by the revision, then accept or return it again.

## Stop conditions

- Accept when the structure is readable, or its irreducible constraint is
  verified and discoverable where the code depends on it.
- Hold when the explanation or evidence is missing. Report the exact open
  question; do not label the implementation ready.
- Reject when complexity is avoidable or its rationale is wrong. Green tests
  cannot waive this gate.

Do not paper over tangled logic with an essay, comment every obvious line, or
demand a redesign merely because a dependency's contract looks unfamiliar.
