---
name: consolidate-test-suites
description: Decide where test coverage belongs for bug fixes and features. Use before adding, moving, or deleting tests after a fix, feature, or architectural change. Select one owning layer, reuse existing canonical suites, preserve distinct stress/adversarial coverage, block weakly placed tests, and remove weaker duplicates. Also loaded by /implement during the coverage step.
---

# Consolidate Test Suites

Purpose: place each invariant in one owning test layer only.

Definitions:

- **Invariant**: the rule that must stay true.
- **Owning layer**: the lowest layer that truly owns and can prove that rule.
- **Canonical suite**: the normal existing suite for that owning layer, including its existing harness, fixtures, and mocks.

Default: reuse an existing canonical suite. Do not create a new standalone regression test unless the exception rule allows it.

## Hard rules

- You MUST identify the invariant before adding or moving any test.
- You MUST identify one primary owning layer: unit, integration, or end-to-end.
- You MUST first try to place coverage in an existing canonical suite for that layer.
- You MUST prefer editing an existing test file over creating a new test file.
- You MUST NOT add the same invariant in multiple layers unless each layer covers a different failure mode; name the distinct failure mode for each you keep. A stress, concurrency, replay, or boundary-input condition counts as distinct from the nominal path, so its test is owned coverage in its own right.
- You MUST NOT add tests that lock in implementation details unless that implementation unit itself owns the invariant.
- You MUST NOT create a standalone regression test because it is faster or easier.
- You MUST reuse the owning layer's existing harness, fixtures, and mocks. Do not build a parallel assertion mechanism for evidence the canonical suite already produces (e.g. scraping a log/state file when the harness already captures the boundary).
- You MUST ensure each placed test can fail. Assert the specific expected value, not that work merely happened. Gate any absence/negative assertion behind a positive completion signal so it cannot pass vacuously (e.g. an absence check that is trivially true because the awaited work has not run yet).
- If you cannot name the invariant and the owning layer, STOP. Report that placement is not justified.

## Required decision order

Choose the first option that fits:

1. Add to an existing test in an existing file in the owning layer.
2. Add a new test to an existing canonical file in the owning layer.
3. Create a new file inside the existing canonical suite in the owning layer.
4. Create a standalone regression-style test only if the exception rule passes.

## Owning layer rules

Choose **unit** when:
- one module owns the rule, and
- the bug reproduces without I/O, transport, persistence, retries, IPC, orchestration, or lifecycle coupling.

Choose **integration** when:
- the rule lives at a boundary between components, or
- the bug depends on serialization, persistence, ordering, replay, retries, IPC, process lifecycle, or multi-component coordination.

Choose **end-to-end** only when:
- the user-visible contract cannot be trusted from lower-layer tests alone, or
- the contract only holds under conditions lower layers cannot reproduce faithfully (real concurrency, cross-process ordering, full transport/serialization round-trips, load).

Tie-breakers:
- If torn between unit and integration, choose integration.
- Never choose end-to-end to compensate for uncertainty.
- Never choose a higher layer just because it is easier to reproduce there.

### Wiring / discovery invariants (the common two-layer case)

When the rule is "X is derived correctly AND X reaches runtime", it has two genuinely distinct failure modes. Split it deliberately; do not duplicate:

- **unit** owns the derivation: the pure resolver that produces X (e.g. which paths, values, or config are computed).
- the **highest harness that observes the wired effect** owns the contract that X actually takes effect (reaches the process, model, request, or UI).

Name both failure modes explicitly. Assert each layer on its own evidence — unit on the returned value, the higher layer on the observable effect captured at the boundary — never the same assertion in both.

## Exception rule for standalone regression tests

A standalone regression-style test is allowed only if ALL are true:

- no existing canonical suite can express the case cleanly
- the reproduction is deterministic
- the case has durable incident or contract value
- adding it to the canonical suite would make that suite less clear

If any condition is false, fold the coverage into the canonical suite.

## Duplicate cleanup

After placing coverage:

1. Search for tests that assert the same invariant.
2. Keep the strongest owned location.
3. Merge any unique assertions into that location.
4. Delete or simplify weaker duplicates (a distinct stress/adversarial case is not a duplicate).
5. Rename tests by behavior and owner, not by ticket number or bug history.

## Verification

Before finishing:

1. Run the narrowest relevant test target first.
2. Confirm each new or edited test can fail — invert the expectation or break the code path once, see it go red, then revert.
3. Run required typecheck, build, or lint steps for touched code.
4. Report exactly what was run and whether it passed.

## Default output format

```
Invariant:
Owning layer: <unit | integration | end-to-end>
Target suite/file:
Action: <reuse existing test | add to existing suite | create file in canonical suite | keep standalone regression>
Why this layer owns it:
Duplicates to merge/delete: <list or "none">
Verification run:
Residual risk: <what is still not covered, if anything>
```
