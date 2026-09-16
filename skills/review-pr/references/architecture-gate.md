# Architecture gate

A phase of first-pass, before detailed verification. One question, answered from **current source**: is this the right shape, or would detailed review of it be wasted? Output: `continue` / `revise` with quoted evidence. Not a correctness review — hunt no defects to justify a ruling, invent no runtime failures. Two seats in parallel: the **main reviewer** (owns the ruling) and the **architecture worker** (§8). Both load **structural-review**.

## 1. Problem and constraints

From ticket, conversation, tests (what they assert), and existing code: required behavior and hard constraints — contracts, invariants, persisted/wire compatibility, performance envelopes, committed API/UX behavior. Never from the PR's mechanism; its framing is a hypothesis.

## 2. Behaviors at the right grain

A behavior is a policy with its own reason to change — which state applies, how an edge case is decided, how a result is coordinated — never a feature or module label. Separating **domain-specific transformation** from surrounding **common behavior** is an aid; the trace, not the label, decides what is common.

## 3. Current-source trace — admission evidence

Read the **current head**. For each behavior or constraint the change touches, find its **current owner or authoritative locus** — the implementation, contract, state representation, config, or document that decides it — and its actual **consumers or readers**, in full. Where the PR touches a dispatch, additionally name the **affected input** and one **concrete other input**, follow the current branch each takes to equivalent output, and quote the **dispatch predicate** and the **remaining range** — first to last statement the other input still traverses, and what it produces. Where no dispatch changes, say so and trace the owner directly; never invent runtime callers for a contract, state, config, or document change — its readers are its consumers. Deleted base code is cited only after this, as history; it never proves current ownership.

Classify the case; the evidence it requires follows it:

- **split** — the affected input leaves at the predicate; others continue through the range. A neutral routing fact, not yet a finding. Rows (§4) come from that range's own coordination, sequencing, and edge decisions — not from domain delegates or downstream leaves.
- **retired** — proven for **all** consumers: no input and no other caller enters the range after the change. A range one route bypasses is not retired because that route's old delegates were deleted.
- **new** — no current owner performed the behavior for any input (owner candidates and their consumers checked).
- **no bypass** — in-place change to a single owner; trace owner and consumers and evaluate the changed state, contract, or mechanism there. Never invent a boundary or sibling, or call behavior the owner already performed new.

Sibling validity (split): the sibling is the other input's current branch through the range, verified in diff **and** callers. Role and call path define "unaffected", not file name. A route this PR migrated is not a sibling; one sharing only a downstream helper proves that helper's ownership, never the range's.

**Admission.** An account is admissible only with the evidence its case requires — split: quoted predicate, remaining range, other input's current branch; retired: the all-consumer proof; new: the owner candidates checked; no bypass: current owner, its consumers, and the changed state, contract, or mechanism. Missing that, or self-contradictory (a range called retired while an input is shown continuing past the predicate), it is **incomplete coverage**: request the missing trace; never reconcile or continue from it. Admission decides only whether judgment may proceed; `continue`/`revise` remain the parent's call.

## 4. Rows and change impact

One row per behavior or constraint the change touches — a handful, not per line: **behavior/constraint → current owner or authoritative locus → consumers/readers → proposed change and its impact**. In a split case the row also records the **deciding loci** on the sibling branch and the affected route. Then ask: **if this same policy changes, which sites must change together?** Two or more sites deciding the **same policy** — same reason to change, shown by tracing what each decides and for whom, not by comparing text — is split ownership, unless a real source constraint (cite it) requires separate owners; that row is **justified** and yields no finding and no consolidation direction. Mechanically identical code is a reason to investigate policy identity, never proof of it: independently owned policies can coincide in text today and must be free to diverge. A shared leaf both copies call proves the leaf's ownership, not the policy's. Copies that instantiate one unjustified split are **one finding** at the split.

Confidence is not severity. An unjustified split of the same policy, established from source, is a **confirmed** structural finding, tiered per **structural-review** (`warning` for a boundary leak or duplicated common behavior, `opinion` for a missed reframing), whatever the gate rules. `candidate` means unresolved evidence, never reluctance to state an opinion.

Hunt prior/parallel art (linked refs, `gh pr list --search "<area>" --state all`): an in-flight PR that subsumes this one is the headline.

## 5. Simplest shape and direction

Write the shape that satisfies §1 with each behavior owned once, preserving the domain core and the PR's contribution. For an unjustified split: where the owner's interface cannot express a required behavior, weigh a minimal interface extension, a common lower-level primitive both routes call, and a separate implementation — by outcome: any extension point is insufficient while a duplicate of the same policy remains. State **one** direction that removes the whole split; never pair it with a bypass alternative that keeps copies. For every other row the direction, if any, addresses the changed owner, contract, state representation, or document structure itself; a shape that stands needs no direction. Set the PR against that shape, the old implementation, and the surviving owner; diff size proves nothing.

## 6. Ruling

`revise` requires all three:

1. a material structural defect shown in source — wrong boundary, the same policy duplicated across unjustified owners (the row's loci), needlessly broad state or contract, avoidable mechanism, unjustified coupling;
2. a concrete direction preserving required behavior, constraints, and contribution — "restore the old code" and "extract a helper" are not directions;
3. adopting it would **materially replace the affected region** — the coordination range, implementation, contract, state representation, or document structure the change owns — so detailed review of that region is wasted. The threshold is that region, not every file: a retained domain core or "the rest still needs review" never defers a material correction.

Insufficient alone: nits, taste, unfamiliarity, diff size, an abstraction that earns its keep, a justified divergence, identical text without demonstrated shared policy, a local predicate extraction, an isolated repeated condition with surrounding coordination intact. Uncertainty gets targeted reads; what they cannot settle is `continue` with a `candidate`, never `revise`.

## 7. Gate report

```text
GATE — PR <number> @ <HEAD_SHA>
Problem: <required behavior> | Constraints: <hard ones>
Case: split | retired | new | no bypass
Owner: <current owner / authoritative locus>; consumers/readers: <list>
Split only (else n/a): dispatch <locus>; predicate "<quoted>" | affected <input → current branch → output> | other <input → current branch → output | none — evidence> | remaining range <first..last statement, what it produces> | sibling verified after change <diff/caller evidence>
Retired: <all-consumer evidence> | New: <owner candidates checked> | else n/a
Rows:
- <behavior/constraint>: owner <locus> → consumers <list> → change <what> → impact <sites that change together>; split only: sibling <file:line, quoted decider> | affected <file:line, quoted decider> — same policy, unjustified | justified: <constraint>
Shape + direction: <one paragraph; one direction for an unjustified split, or the changed owner/contract/document itself, or none>
Ruling: continue | revise — <reason citing rows>
Severe defects observed en route (not hunted): <none | list>
```

A `continue` quotes loci or verified absence/necessity; assertion is not a report.

## 8. Architecture worker — bounded assignment

Dispatch as `subagent_type: astra`, heavy — a read-only structural specialist, not an orchestrator (it loads no orchestration skill and delegates nothing). If that subagent type is unavailable, the parent reports a specialist blocker at the gate; it never downgrades silently, and a missing report is never counted as `continue`. Load this file and **structural-review** only — never `first-pass.md`. This is a parent-scoped structural assignment on one boundary, not a survey of the PR.

**Inputs — the current-source slice** (parent-selected, current head): the primary changed boundary or authoritative locus — the shared caller/owner for a routing change; otherwise the changed implementation, contract, state model, config, or document — as whole files; its affected direct delegate(s); the concrete surviving consumer or branch through that owner when one exists, otherwise its actual consumers or readers (no fabricated branches or runtime callers); the narrow contracts needed to read those paths; plus PR target, `HEAD_SHA`, the parent's §1 statement if formed, and ledger candidates if any. The slice states source facts and verified constraints — which inputs take which call paths — never an expected finding or desired ruling.

**Work.** Read the slice's files whole first; follow dependencies outward only as far as settling an architectural question requires, and go wherever contrary evidence leads — the slice bounds where you start, not what you may conclude. Do §1–§6 from current source (read-only; no probes, no tracked-file writes), using diff and base afterwards for scope and lineage. Return the "Gate report" above and **stop**. No correctness review, tests, or CI triage; note severe defects only if seen. Your report covers the slice's locus; it implies nothing about untouched surfaces. The parent admits ("Admission", §3) and reconciles before any `continue`; the ruling is the parent's.
