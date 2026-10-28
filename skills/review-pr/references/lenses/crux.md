# Crux lens

Build the best solution to a problem from first principles, so every mechanism in a solution, a design's or a PR's, traces to the problem's core or to a named constraint. `workflows/ground-up.md` always runs it; the architecture gate runs it on the `crux` keyword (`lenses/architecture.md` §5); `/implement` runs it in its design phase. Loads **zoom-out** (step 1) and **patch-coherence** (step 4).

## 1. Map

Load **zoom-out** on the area: modules, owners, callers, and the domain vocabulary. Map the base revision when the solution must not see a PR.

## 2. Crux

```text
Crux: <the problem in one or two sentences, no mechanism>
Done means: <observable behavior that proves it solved>
Hard constraints: <contracts, persisted or wire compatibility, performance envelope, platforms, product commitments; source for each>
Surface: <owners and consumers the problem lives in, with paths>
```

Facts and constraints only, never an expected design. A constraint without a source is a guess about reality: find the source or drop it.

## 3. Pure solution

Solve the crux alone: no codebase, no constraints, no migration. Name its core mechanisms (`M1`, `M2`, …), the smallest set that delivers *done means*, with the invariant each holds and a **show-me** view of their shape. This is the yardstick, not something expected to ship.

## 4. Layers of reality

Add one constraint at a time, hardest first: contracts and persisted or wire data, then platforms and performance envelopes, then product commitments, then conventions and ergonomics. A soft constraint must never take credit for a mechanism a hard one already forced.

Before adding anything for a layer, ask **patch-coherence**'s layer-subsumption question against the mechanisms so far: can an existing mechanism absorb this constraint, and would one new mechanism replace two earlier ones? Only then add the least mechanism that satisfies it.

```text
Layer <n>: <constraint> — source <ref>
  forces: <what the solution can no longer do, or must now also do>
  mechanism: <absorbed by M<k> | new M<k> | M<k> replaces M<i>, M<j> | nothing forced>
```

A layer that forces nothing still gets its row: it proves the constraint was checked.

## 5. Layer ledger and complexity accounting

The optimal solution is the pure core plus the layers' mechanisms: the **layer ledger**. Every mechanism in it traces to the core or to one or more layers.

Judge any other solution against the ledger, a PR's included, by mapping each of its mechanisms to a ledger row:

- A mechanism that traces to no row is **accidental complexity**: a structural finding, tiered per `lenses/structure.md`.
- A core mechanism or forced layer the solution lacks is a **gap**, tiered by what it leaves unsolved.

Each finding cites the ledger row it rests on.
