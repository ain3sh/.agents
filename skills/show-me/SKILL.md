---
name: show-me
description: Select and render one compact visual representation from verified evidence when code shape, control flow, state, ownership, dependencies, or a before/after change is clearer than prose. Use when the user invokes /show-me or asks to see rather than read an explanation.
argument-hint: [target] [as <form>]
user-invocable: true
---

# Show Me

Show-me is a transformation layer: preserve the evidence, choose the shape that
makes its structure obvious, render it inline, then state the implication once.

## Act

| Goal | Action |
|---|---|
| Answer `/show-me` | Resolve the target from arguments or the current topic, verify the source facts, then load `references/representations.md` and choose one form. |
| Compress an existing explanation | Transform the evidence already established in the conversation; do not restart the analysis. |
| Compose from another workflow | Consume that workflow's verified trace, concern map, diff analysis, or design decisions; obey its tighter line and surface limits. |
| Honor `as <form>` | Use the requested form when it can represent the evidence without distortion; otherwise name the mismatch and use the closest lossless form. |
| Produce a polished artifact | Select the information shape here, then hand rendering to `plannotator-visual-explainer`, `design-doc`, `excalidraw`, or the owning artifact workflow. |

## Detect

Use show-me when at least one is true:

- prose is describing more than two actors, transitions, modules, or dependencies
- order, topology, ownership, state, or a before/after delta carries the point
- the reader needs code shape before implementation or review
- the user says "show me", "visualize this", or asks for a specific form

Do not use it for uncertainty, rationale, trade-offs, evidence quality, or a
simple fact that one sentence communicates better.

## Output contract

```text
<specific label>

<one inline representation>

Implication: <one sentence>
```

- Direct `/show-me`: normally at most 40 lines.
- Embedded in another workflow: at most 20 lines unless that workflow says less.
- Omit the implication when the representation already states it explicitly.

## Rules

1. Never visualize unverified structure -- reread the relevant source, diff, or trace first.
2. Never use a picture to conceal uncertainty -- mark unknown edges or omit them.
3. Never emit multiple competing views of the same fact -- one question gets one representation.
4. Never default to HTML, Mermaid, images, or generated files -- Markdown, ASCII, diff fences, and typed signatures are the fast path.
5. Never use anonymous boxes when real symbols, actors, files, states, or data labels are known.
6. Never narrate the representation afterward -- state only the consequence prose adds.
7. Never turn show-me into a second analysis pipeline -- the owning workflow establishes facts; this skill changes their representation.
8. Never simplify away a transition, dependency, or state needed to preserve the owning workflow's invariant.

## Failure map

| Symptom | Action |
|---|---|
| Diagram is a decorated paragraph | Replace it with a call tree, state table, responsibility tree, or structural diff. |
| Visual and prose say the same thing | Delete the prose; keep one implication sentence if needed. |
| Representation needs a legend to be understood | Use concrete labels or choose a simpler form. |
| More than one form seems useful | Pick the form that answers the user's question; offer another only on request. |
| Inline output is too dense | Reduce scope, not font size; escalate to the owning artifact workflow only when the detail is essential. |
| Requested form would misstate the system | Name the mismatch in one sentence and use the closest lossless form. |
| User requests `as html` | Select the shape here, then load `plannotator-visual-explainer`; use `design-doc` instead only for a full RFC, memo, or sync brief. |
| A sequence arrow has an ambiguous endpoint | Replace fixed-width lifelines with the numbered actor-message grammar in `references/representations.md`. |

## References

Load on demand; do not reabsorb into this file:

- `references/representations.md` — selection matrix, inline grammars, and fidelity checks.
