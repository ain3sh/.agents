---
name: show-me
description: Select and render one compact visual representation from verified evidence when code shape, control flow, state, ownership, dependencies, or a before/after change is clearer than prose. Use when the user invokes /show-me or asks to see rather than read an explanation.
argument-hint: [target] [as <form>]
user-invocable: true
---

# Show Me

Make a verified relationship or code shape readable off the page: name the
reader's question, choose the view, then render and check it for its destination.

## Act

| Goal | Action |
|---|---|
| Answer `/show-me` | Resolve the target from arguments or the current topic and reread its source. Write the one question the reader needs answered, then choose the view with `references/representations.md`. |
| Compress or compose | Transform evidence already established by the conversation or the owning workflow (trace, concern map, diff analysis, design decisions); do not restart the analysis; obey that workflow's budget and destination. |
| Honor `as <form>` | Use the requested form when it represents the evidence without distortion; otherwise name the mismatch in one sentence and use the closest lossless form. |
| Render or embed a visual explanation | Load `references/surfaces.md`: terminal text, GitHub Mermaid/code or images, browser HTML/SVG, and reused Excalidraw renders. |
| Compose into a PR or design doc | Take the caller's verified facts, reader question, destination, and theme/components. Return the checked view and any necessary code companion; the caller owns section placement, document-wide checks, and authorized publishing. |
| Answer a simple fact | One sentence, no view. |

## Detect

Use show-me when prose is juggling more than two actors, transitions, modules,
or dependencies; when order, topology, ownership, state, or a before/after delta
carries the point; or when the reader needs code shape (types, signatures,
control structure) before implementing or reviewing. Uncertainty, rationale,
trade-offs, and evidence quality stay prose.

## Output

```text
<label naming the question or relationship>
<primary view>
<optional code companion: one typed block for a detail the view cannot hold>
Implication: <one sentence, only when it adds a consequence the view does not state>
```

Accept the view only when all three hold:

- **Recoverable**: the reader reads the relationship off the view instead of
  reconstructing it from sentences; every indentation, arrow, row, and diff
  line encodes a relation they can follow (call nesting, containment,
  ownership, sequence, decision, transition, dependency). Branches that merely
  enumerate what a node also does are a bullet list; fitting a budget proves nothing.
- **Faithful**: every node, edge, type, and line traces to source reread now;
  unknown edges are marked or omitted; quoted code carries its path; pseudocode,
  illustrative blocks, and elisions are labelled.
- **Renders**: the destination displays the grammar and the view stays legible
  at its width (`references/surfaces.md`).

If the relationship is not recoverable or faithful, narrow it or omit the view.
If rendering is blocked, label the draft unverified; do not present it as checked.
One primary view per question; multiple questions can earn complementary views,
not duplicate illustrations. Inline text budgets are roughly 40 lines direct
or 20 embedded, unless the caller says otherwise. HTML has no source-line budget.

## Rules

1. Never run a second analysis pipeline; the owning workflow establishes facts,
   this skill changes their representation.
2. Never simplify away a transition, dependency, or state the owning workflow's
   invariant depends on.
3. Never treat rendering as publishing permission. Hand files to the caller;
   its authorized publish step owns uploads and external writes.

## Failure map

| Symptom | Action |
|---|---|
| View is a decorated paragraph, or a list dressed as a tree or diff | Name the relation the reader must hold (calls, containment, order, state, dependency) and draw that with real symbols; if there is none, drop the view. |
| Visual and prose say the same thing | Delete the prose; keep one implication sentence if needed. |
| Two views overlap | Keep the clearer one. A second view must answer a distinct reader question; a code companion fills a detail the primary view cannot hold. |
| Inline output too dense | Reduce scope, not font size; move to a browser HTML view only when the detail is essential. |
| Mermaid or HTML would land in a plain terminal | Use the terminal grammar in `references/surfaces.md`. |
| Output is a full walkthrough or RFC | Cut to one view; `/explain-diff` owns walkthroughs, `design-doc` owns RFCs and memos. |

## References

Load on demand; do not reabsorb into this file:

- `references/representations.md`: question-to-view matrix, layout gate, grammars, code fidelity, companion.
- `references/surfaces.md`: rendering, themes, embedding, source access, checks, and local handover.
- `references/replay.md`: behavioral replay scenarios and grading.
