---
name: consolidate-test-suites
description: Decide where test coverage belongs, and cut test suites down to what actually defends the change. Use before adding, moving, or deleting tests after a fix, feature, or refactor, and whenever a diff is test-heavy or hard to review. Journeys first, one owning layer per invariant, a junk taxonomy for deletion, preserved stress/adversarial coverage, and a measured audit mode. Also loaded by /implement during the coverage step.
---

# Consolidate Test Suites

A test is a liability until it proves otherwise. It costs review time, CI time, and refactor friction forever. It earns its place only by pinning an invariant that would otherwise break silently, at the one layer that owns it.

Target: **the smallest suite that defends the change just as well.** A PR drowning in tests gets skimmed, not reviewed, so an unreviewed test defends nothing.

## Stance

1. **Journeys first.** Start from the handful of real user journeys the change enables or protects. One deterministic journey test that walks a user path end to end (open → act → observe → recover) replaces a dozen unit tests that each poke one prop through a mock.
2. **Units for what journeys can't pin.** Keep a unit or integration test only for an invariant a journey cannot hit deterministically: race and ordering windows, durable-before-acknowledged ordering, replay/dedupe idempotency, failure and rollback paths, pure math (sizing, offsets, parsing), and protocol/schema contracts.
3. **Stress is its own owner.** Concurrency, replay, malformed input, boundary sizes, and scale are distinct failure modes from the nominal path. Their tests are owned coverage, never duplicates to delete.
4. **One invariant, one owner.** The same rule asserted at two layers is a duplicate unless each layer catches a different failure mode you can name.
5. **Every kept test states its invariant in one line.** If you cannot write that line, delete the test.

Definitions: an **invariant** is the rule that must stay true. The **owning layer** is the lowest layer that truly owns and can prove it. The **canonical suite** is that layer's existing suite, with its harness, fixtures, and mocks. A **journey** is a user-observable path driven through the real boundary (CLI/TUI harness, protocol client, browser) with deterministic inputs (mock LLM fixtures, recorded responses).

## Pick the mode

- **Place**: you are about to add a test for a fix or feature. Go to [Place](#place).
- **Audit**: the diff already has tests. Audit when any of these holds:
  - test lines exceed production lines;
  - a refactor deleted or merged a mechanism;
  - reviewers push back on size;
  - you inherited a branch.
  Go to [Audit](#audit).
- Both: audit first, then place the gaps the audit exposed.

## Layer rules

Choose **unit** when one module owns the rule and it reproduces without I/O, transport, persistence, retries, IPC, orchestration, or lifecycle coupling.

Choose **integration** when the rule lives at a boundary between components, or depends on serialization, persistence, ordering, replay, retries, IPC, process lifecycle, or multi-component coordination.

Choose **end-to-end / journey** when:
- the contract is user-visible and cannot be trusted from lower layers alone;
- the contract only holds under conditions lower layers cannot fake faithfully (real concurrency, cross-process ordering, full transport round-trips);
- or a single journey replaces several lower-layer tests that each re-assert one step of it.

Tie-breakers:
- Torn between unit and integration: choose integration.
- Never choose e2e to compensate for uncertainty, or because it is easier to reproduce there.
- A journey must be deterministic. Flaky e2e is worse than none: fix the determinism (fixtures, explicit waits on observable state) or pick another layer.

**Wiring invariants** ("X is derived correctly AND X reaches runtime") have two distinct failure modes; split them deliberately:
- a unit test owns the derivation, asserting on the returned value;
- the highest harness that observes the wired effect owns the "takes effect" contract, asserting on the boundary capture.
Never make the same assertion in both.

## Junk taxonomy: delete on sight

These fail the "names an invariant that can fail" bar. Delete them unless the test is the only owner of a real invariant hiding behind the bad shape. In that case rewrite it into a correct shape.

| Pattern | Tell |
|---|---|
| **Self-mocked SUT** | The test mocks the module the unit depends on and re-implements its logic in the mock (e.g. a filtering store mock under a hook that filters). It tests the mock. |
| **Mock echo** | It asserts that a mock returned what it was configured to return, or was called with the args the test just passed in. |
| **Implementation-detail assertions** | Call order on internal mocks, private state, which helper ran, intermediate render counts. Refactor-hostile, behaviour-blind. |
| **Prop plumbing** | Asserts that prop `a` reaches child prop `a`. The type system plus one journey covers it. |
| **Copy / i18n / snapshot text** | Asserts exact strings or big snapshots with no behaviour behind them. Translation-completeness gates already exist. |
| **Journey fragments** | Each test re-asserts one step of a flow an e2e journey already walks. |
| **Dead mechanism** | It tests a component, option, or path that no longer exists, or only exists for the test (a test-only export). |
| **Type-guaranteed** | It asserts what the compiler already enforces, `typeof x === 'function'`, or that an import exists. |
| **Unfalsifiable** | An absence check not gated behind a positive completion signal, a loop assertion over a possibly empty set, or `expect(true)`. |
| **Near-duplicate cases** | Five `it`s differing by one input. Collapse them into one `it.each`, or keep the most adversarial case. |

CI-gated artifacts (ownership/export snapshots, registry parity tables, pack smoke tests) stay, but kept to the minimal entries the change needs.

## Place

1. Name the invariant and the owning layer. If you cannot, STOP: placement is not justified.
2. If the invariant belongs to a user journey, extend the journey test that owns that path first (add a step or an assertion) before writing anything new.
3. Otherwise use the first option that fits:
   1. add to an existing test in an existing file of the owning layer;
   2. add a new test to an existing canonical file;
   3. create a new file inside the canonical suite;
   4. create a standalone regression test, only if ALL of these hold: no canonical suite can express it cleanly, it is deterministic, it has durable incident or contract value, and folding it in would make the suite less clear.
4. Reuse the owning layer's harness, fixtures, and mocks. Never build a parallel assertion mechanism for evidence the harness already captures.
5. Assert the specific expected value, not that work happened. Gate every negative assertion behind a positive completion signal.
6. Add stress/adversarial cases as their own tests when the contract must hold under them.

## Audit

Run this over a diff (`<base>` = the merge base), a directory, or a suite.

1. **Measure.** Split the diff into test and production lines:
   ```bash
   git diff <base> --numstat | awk '$3 ~ /(\.test\.|\.spec\.|e2e|__tests__|\/tests?\/)/ {t+=$1} $3 !~ /(\.test\.|\.spec\.|e2e|__tests__|\/tests?\/)/ {p+=$1} END {print "test +"t"  prod +"p}'
   ```
   Rank test files by added lines. More test lines than production lines is a strong audit signal. Unless the change is a pure safety net for untested legacy code, target at least a 50–60% cut of added test lines.
2. **List the journeys.** Write the 3–7 user journeys the change must keep working, and map each to an existing e2e test (or mark it as a gap). This list is the yardstick for "covered elsewhere".
3. **Triage every added or modified test** as DELETE (junk taxonomy, or covered by a listed journey or a kept test), KEEP (a one-line invariant that no journey pins deterministically), or COMPRESS (keep the invariant, cut the bulk). Tests that predate the change stay unless the change altered the behaviour they cover; then update them minimally.
4. **Before each delete**, confirm the invariant is either worthless or covered elsewhere. If it is real and uncovered, add it to the journey gaps; never delete it silently.
5. **Port, don't transplant.** When a refactor folds mechanism A into canonical primitive B, move only A's genuine invariants into B's canonical suite, rewritten against B's API. Delete A's test file; do not keep a renamed copy.
6. **Fill the journey gaps.** Extend existing e2e files; each new journey walks a real path with several observations. Prefer 1–3 excellent journeys over broad scatter.
7. **Sweep the leftovers.** Delete test-only exports, fixtures, and helpers the deletions orphaned (run knip or an equivalent). Remove comments that describe deleted tests.
8. **Split large audits** by file ownership (e.g. daemon, services, UI, frontend), with one worker per area sharing the same rubric and the journey list. No two workers edit the same file. Each reports before/after numstat.

## Hard rules

- Name the invariant and owning layer before adding, moving, or keeping any test.
- Reuse an existing canonical suite before creating a file; extend a journey before adding units for its steps.
- Never assert the same invariant at two layers unless each catches a distinct, named failure mode.
- Never delete stress, concurrency, replay, boundary, or failure-path coverage as a "duplicate" of the nominal path.
- Never lock in implementation details unless that unit itself owns the invariant.
- Every placed or kept test must be able to fail: break the code path or invert the expectation once, see red, then revert.
- Never write a standalone regression test because it is faster or easier.

## Verification

1. Run the narrowest target first: every touched test file, then the journey suites you extended.
2. Red check each new or edited test once.
3. Run the typecheck, lint, and knip steps for touched packages.
4. Report exactly what ran and whether it passed.

## Output

Place:

```
Invariant:
Owning layer: <unit | integration | end-to-end/journey>
Target suite/file:
Action: <extend journey | reuse existing test | add to existing suite | create file in canonical suite | keep standalone regression>
Why this layer owns it:
Duplicates merged/deleted: <list or "none">
Verification run:
Residual risk:
```

Audit:

```
Test lines: +<before> → +<after> (<pct> cut); production: +<n>
Journeys: <journey> → <e2e test | GAP filled in <file>>
Per file: <file>  +<before> → +<after>
  kept: <one-line invariant> (× each)
Moved to journeys: <invariant → journey>
Orphans removed: <helpers/exports/fixtures>
Verification run:
Residual risk:
```
