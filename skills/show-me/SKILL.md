---
name: show-me
description: "Use for /show-me, when the user asks to see rather than read, or when a reply about 3+ actors or states turns into prose: diagram from verified evidence."
argument-hint: "[target] [as <form>]"
user-invocable: true
---

# Show Me

Make a verified relationship or code shape readable off the page. Name the one
question the reader has, reread the source, draw the smallest view that answers
it, and keep prose to the sentence the view cannot carry.

## Act

Pick the shape from the question. Every example below is illustrative; real
views carry real symbols and paths (`references/representations.md`).

**What does it do?** Pseudocode: decisions, mutations, return shape; drop
language ceremony.

```text
on(save)
  if content is unchanged
    return cached result
  write new content
  return fresh result
```

**What calls what?** Call tree: indentation means "called by"; mark changed or
failing edges; label async, conditional, retry, and fan-out edges.

```text
handleCreateSession                  routes/session.ts
  validateRequest
  SessionStore.insert
  publish(session.created)
    AgentWorker.run                  worker.ts   ← new owner
      loadContext
      callModel
      persistResult
```

**How is the UI composed, where does state live?** Component tree in JSX, with
only the state owners and boundaries the question needs.

```tsx
<SessionPage>                        {/* apps/web/routes/session.tsx */}
  useSessionEvents()
  <SessionToolbar>
    <RunSkillButton />               {/* packages/ui */}
  <SubmitBoundary>                   {/* state: submit result */}
```

**Where does each responsibility live?** Shallow file tree, one responsibility
per line; `+ ~ #` annotations carry what changed.

```text
src/
├── commands/        parses user actions
├── sessions/        owns session state
│   └── store.ts     + readingFocusByArtifactId, publishReadingFocus()
└── transport/       sends API requests; ~ retries moved here from commands/
```

**Who acts in what order? How can state change?** Sequence or state diagram
(numbered text in a terminal, Mermaid on GitHub or in a browser); grammars and
actor rules in `references/representations.md`.

**What changed?** A `diff` fence over the shape that already exists, when most
of it is unchanged. Match the diff to the topic: call tree, file tree,
component tree, or pseudocode.

```diff
 handleCreateSession
   validateRequest
+  enforceQuota
   SessionStore.insert
   publish(session.created)
     AgentWorker.run
       loadContext
+        fetchPriorTurns
       callModel
       persistResult
+        emitUsageEvent
```

**What shape should the code have?** Types and signatures, the whole block when
most of it is new or the reader needs a copyable target.

```ts
type JobState =
  | { status: "queued" }
  | { status: "running"; owner: WorkerId }
  | { status: "done"; result: Result }

run(job: QueuedJob): Promise<DoneJob>
```

**What happens to each surface now?** Policy before/after table: one row per
surface, old mechanism and limit, new limit and pointer, owning commit; the
surprise row marked (`references/representations.md`).

**Too dense for text or Mermaid?** One focused HTML file (diagram, explainer,
mockup) in the product's colors and type with real labels, then open it or
hand it to the caller (`references/surfaces.md`).

Use one view per question. Several questions earn several views: a tree beside
the diff that changes it is normal; a code companion (one typed block) fills a
detail the view cannot hold. Scope decides size: keep every call, file, state,
and boundary the question needs and nothing it does not.

| Situation | Action |
|---|---|
| `/show-me [target] [as <form>]` | Resolve the target from arguments or the current topic, reread its source, write the reader's question, choose the shape above. Honor `as <form>` unless it would distort the evidence; then name the mismatch in one sentence and use the closest lossless form. |
| Compose into a PR, design doc, or review | Take the caller's verified facts, reader question, destination, and theme; return the checked view and any companion. The caller owns placement, document-wide checks, and publishing. Do not restart its analysis. |
| Render or embed | `references/surfaces.md`: terminal text, GitHub Mermaid/code/images, Slack images, browser HTML/SVG, reused Excalidraw renders. |
| A simple fact | One sentence, no view. |

## Detect

Draw when prose is juggling more than two actors, transitions, modules,
dependencies, or surfaces; when order, topology, ownership, state, or a
before/after delta carries the point; or when the reader needs code shape
(types, signatures, control structure) before implementing or reviewing.
Uncertainty, rationale, trade-offs, and evidence quality stay prose.

## Reply shape

```text
<label naming the question or relationship>
<view>
<optional code companion>
Implication: <one sentence, only when it adds a consequence the view does not state>
```

## Check before sending

- **Recoverable**: every indentation, arrow, row, and diff line encodes one
  relation the reader can follow (call nesting, containment, ownership,
  sequence, decision, transition, dependency). Branches that enumerate what a
  node also does are a list, not a tree.
- **Faithful**: every node, edge, type, and quoted line traces to source reread
  now; unknown edges are marked `order unverified` or omitted; quoted code
  carries its path; pseudocode and proposed shapes are labelled.
- **Renders**: the destination displays the grammar and the view stays legible
  at its width (`references/surfaces.md`). If rendering is blocked, label the
  draft unverified.

Omit a view only when the diff has no relation to draw (several unrelated
concerns); say so and let the owning workflow omit its section.

## Rules

1. Never run a second analysis pipeline; the owning workflow establishes facts,
   this skill changes their representation.
2. Never simplify away a transition, dependency, or state the owning workflow's
   invariant depends on.
3. Never shrink a view to a line budget or drop it over one unverified detail;
   cut scope the question did not ask for, and mark the unknown.
4. Never treat rendering as publishing permission. Hand files to the caller;
   its authorized publish step owns uploads and external writes.

## Failure map

| Symptom | Action |
|---|---|
| Reply is a wall of prose about several actors, with a view as an afterthought | Lead with the view; keep the one sentence it cannot carry. |
| View is a decorated paragraph, or a list dressed as a tree or diff | Name the relation the reader must hold and draw that with real symbols; if there is none, drop the view. |
| Visual and prose say the same thing | Delete the prose; keep one implication sentence if needed. |
| Two views answer the same question | Keep the clearer one; a companion fills a detail, it does not repeat the view. |
| Inline output too dense | Reduce scope, not font size; move to a browser HTML view only when the detail is essential. |
| Mermaid or HTML would land in a plain terminal | Use the terminal grammar in `references/surfaces.md`. |
| Panels, a table, or a wide tree would land in Slack as a code block | Send an image (`references/surfaces.md#slack`). |
| Output is a full walkthrough or RFC | Cut to the views; `/explain-diff` owns walkthroughs, `design-doc` owns RFCs and memos. |

## References

Load on demand; do not reabsorb into this file:

- `references/representations.md`: question-to-view matrix, layout gate, code fidelity, companion, and the grammars that need rules (sequence, state, dependency, causal, quantitative, policy before/after, graphical panels).
- `references/surfaces.md`: rendering per destination (terminal, GitHub, Slack, browser), PNG capture, themes, embedding, source access, checks, and local handover.
- `references/replay.md`: behavioral replay scenarios and grading.
