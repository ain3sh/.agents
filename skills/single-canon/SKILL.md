---
name: single-canon
description: Enforce a single-canonical-codepath policy -- keep one canonical implementation, delete compatibility, migration, fallback, adapter, coercion, and dual-shape code, and keep contract grammar minimal (no derivable fields, synonym states, dual shapes, or over-wide unions). Use when defining or altering schemas, contracts, persisted state, routing, configuration, feature flags, enum/value sets, or architecture.
---

# Single Canon

One rule, two directions: delete the second word for an old job (legacy shapes, compat paths), and never mint a second word into the new grammar (derivable fields, synonym states, dual shapes). Keep one canonical codepath. Do not preserve draft or legacy behavior unless there is concrete evidence of a real external compatibility boundary.

## Default assumption

Treat previous shapes as internal draft shapes unless there is concrete evidence they are already:

- persisted external or user data
- on-disk or database state that must still load
- a wire format used across process or service boundaries
- a documented or publicly supported contract
- actively depended on outside the refactor boundary

Mere existence of old code is not proof of a compatibility obligation.

## Hard rules

Apply in order:

01. Do not add fallback behavior.
02. Do not add compatibility branches.
03. Do not add shims, adapters, coercions, aliases, or dual-shape support.
04. Do not add fail-fast guards whose purpose is to detect or reject old shapes.
05. Do not add tests whose purpose is to assert rejection of old or legacy shapes.
06. Prefer deleting old-shape handling over preserving or policing it.
07. Update producers, consumers, fixtures, and tests to use only the canonical shape.
08. Remove dead code, dead conditionals, obsolete comments, and translation helpers related to old shapes.
09. Keep validation only for the current canonical contract. Validation may reject malformed current-shape input, but must not branch on legacy discriminators, old field names, aliases, old enum members, or draft formats.
10. When choosing between backward compatibility and simplification, choose simplification.

## Grammar audit -- the canonical shape itself

The hard rules delete legacy vocabulary; this audit stops redundancy from being minted into the new contract. Treat the contract as a CFG: **minimal vocabulary, maximally expressive language**. Target: the smallest grammar that still expresses every distinct state. Run it on any contract you define or alter -- type, schema, enum, union, wire format, config shape -- when it is first drafted and again before commit (a late catch retrofits every producer, consumer, and test):

1. **No derivable fields.** A field computable from another field or discriminant is deleted, not stored (`stop: boolean` beside a `status` where `stop === (status !== 'continue')` -- consumers branch on `status`).
2. **No synonym states.** Two enum/union members no consumer distinguishes collapse into one.
3. **No dual shapes.** One type per meaning. An internal-vs-serialized split must be forced by an actual serialization boundary (non-serializable members, a real wire format); otherwise collapse to the one shape both sides use.
4. **Exact unions.** Every member reachable, every reachable state a member. A state enters the union as an explicit literal, never by riding a broader schema that happens to admit it.
5. **Discriminant-gated optionality.** A field present only in some states hangs off the discriminant (discriminated union, conditional schema), not blanket-optional on the whole shape.

Litmus per field and member: *can any consumer observe a difference if this is removed or derived?* If no, delete it and propagate the reduced grammar through the workflow below.

## Execution workflow

1. Identify the canonical target shape and run the grammar audit on it.
2. Trace every producer and consumer of that shape.
3. Update all live codepaths to emit and consume only the canonical shape.
4. Update fixtures, test data, builders, and snapshots to the canonical shape.
5. Delete legacy handling, branching, comments, and helpers.
6. Keep only current-shape validation that is still required for correctness.
7. If a real external compatibility boundary exists, isolate it and call out the exact file, function, boundary, and reason it cannot be removed yet.

## Ship gate

Same bar whether writing or reviewing -- confirm before delivering, reject on violation:

- One owner for the canonical contract; producers, consumers, fixtures, and tests all speak only it.
- The contract's grammar is minimal: no derivable fields, synonym states, dual shapes, or accidentally-wide unions.
- No old-shape behavior behind conditionals; no translation layers between shapes.
- No validation branches, runtime logic, or tests whose purpose is recognizing or rejecting legacy shapes.
- Dead helpers, obsolete legacy-shape tests, and comments describing removed shapes are gone.
- The diff is minimal: canonical implementation plus canonical tests, nothing else.

## Exception rule

Make an exception only when removing the old shape would break already persisted external or user data, on-disk or database state, cross-boundary wire formats, or a real public contract.

If such a boundary exists:

- do not invent new compatibility layers elsewhere
- name the exact file and function
- describe the concrete persisted or public dependency
- limit any compatibility discussion to that boundary only
