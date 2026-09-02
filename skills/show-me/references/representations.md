# Representation selection

Choose the form from the information structure, not from visual novelty.

## Selection matrix

| Question | Form | Required content |
|---|---|---|
| Where does each responsibility live? | Responsibility tree | real files/modules plus one responsibility each |
| How is a UI composed and where does state live? | Component/state tree | real components, state owners, meaningful boundaries |
| What calls what? | Call tree | real symbols; mark changed or failing edges |
| Who acts in what order? | Sequence | actors, ordered messages, relevant payload/state |
| How can state change? | State transition table | prior state, event, next state, invariant |
| How does an algorithm transform input? | Typed pseudocode | control structure, mutations, return shape |
| What code shape should exist? | Types and signatures | minimal types, function boundaries, ownership |
| What structurally changes? | Before/after diff | unchanged context plus only the meaningful delta |
| Which work depends on which? | Dependency graph | nodes, directed edges, independent branches |
| Which path produced the failure? | Causal flow | expected path, first wrong edge, downstream symptom |

Prefer the narrowest form that answers the question. A table is visual when
alignment carries meaning; an elaborate diagram is not inherently better.

## Inline grammars

### Responsibility tree

```text
feature/
├── route.ts       request boundary
├── service.ts     canonical orchestration
└── repository.ts  persistence only
```

Keep the tree shallow. Include only paths needed to explain ownership.

### Component/state tree

```text
CheckoutPage
├── CartSummary          props: items
├── PaymentForm          owns: payment draft
└── SubmitBoundary       reads: cart + payment
    └── ErrorNotice      state: submit result
```

Include only state and boundaries that affect the question. Do not reproduce
the full DOM or component catalog.

### Call tree

```text
handleRequest()
└── resolveTarget()
    ├── loadItems()
    └── selectCandidate()  ← changed
```

Use indentation for synchronous ownership. Label async, conditional, retry, or
fan-out edges explicitly rather than implying ordinary calls.

### Sequence

```text
1. User   → Client: click submit
2. Client → API:    POST /jobs
3. API    → Queue:  enqueue(jobId)
4. API    → Client: 202 { jobId }
5. Queue  → Worker: deliver(jobId)
```

Use a sequence only when order across actors matters. Put payloads or state
changes on arrows; omit actors that do no work. Use this numbered message
grammar for inline output. Do not draw fixed-width lifelines: label width and
wrapping can make an arrow appear to land on the wrong actor.

### State transition table

```text
| Before  | Event       | After   | Invariant                 |
|---------|-------------|---------|---------------------------|
| queued  | worker owns | running | one owner                  |
| running | succeeds    | done    | result persisted before UI |
```

Do not collapse distinct states merely to make the table shorter.

### Typed pseudocode

```ts
for (const item of items) {
  if (!eligible(item)) continue
  candidates.push(score(item))
}

return maxBy(candidates, candidate => candidate.score)
```

Show the algorithm's decisions, mutations, and output. Omit language-specific
ceremony unless it changes behavior.

### Types and signatures

Use a typed fence even for pseudocode so syntax highlighting preserves shape:

```ts
type JobState =
  | { status: "queued" }
  | { status: "running"; owner: WorkerId }
  | { status: "done"; result: Result }

run(job: QueuedJob): Promise<DoneJob>
```

Show only fields consumers can observe. Prefer one canonical type per meaning.

### Before/after structural diff

```diff
 request
-└── route owns retry + persistence + response
+└── runner
+    ├── owns retry + persistence
+    └── returns final result to route
```

Use diff syntax when most structure is unchanged. Do not reproduce a source
diff unless source text itself is the point.

### Dependency graph

```text
PR 1: contract ──> PR 2: producer ──> PR 3: consumer

PR 4: docs/tests   (independent)
```

State atomic groups explicitly. Never draw an edge merely because one PR is
planned earlier.

### Causal flow

```text
Expected: command → canonical runner → child group → complete evidence
                                  ×
Observed: command → detached shell → truncated log → false failure
                         ↑ first wrong edge
```

Mark the first unintended transition, not only the visible error.

## Fidelity check

Before emitting:

1. Every node and edge traces to verified evidence.
2. Direction means exactly one thing throughout.
3. Unknowns are visibly unknown; absence is not presented as proof.
4. The representation preserves every state or dependency needed for the claim.
5. Removing any remaining node would make the answer incomplete; otherwise remove it.
6. The implication adds a consequence, not a prose transcription of the visual.
