---
name: patch-coherence
description: "Use when two or more candidate fixes or RCAs are on the table, earlier fixes to the same symbol included: check shared root causes, touch sites, and redundancy before recommending any."
---

# Patch Coherence

Run when a workflow has produced **>=2 RCAs or fix proposals** and is about to write each into its own recommendation block (e.g., `/address-review` after step-3 per-thread RCAs, `/implement` on a ticket with >=2 distinct bugs). Skip with one fix candidate.

**Earlier fixes are candidates too.** On a branch, every prior fix commit to the symbol a new finding targets is on the table. One new finding at a symbol that already took >=2 fixes is a **recurrence** and runs the audit:

```bash
git log --format='%h %s' -s -L ':<symbol>:<file>' <base>..HEAD
```

Per-item RCAs compound badly: five reviewer comments produce five locally-minimal patches that may share a root cause, touch the same module five different ways, or all collapse into one upstream change -- the fix lands at five wrong layers instead of one right one. The audit must run **before** per-item recommendations are committed; post-hoc reflection rubber-stamps already-written blocks.

## The four-question audit

Answer all four explicitly. Name the items in any "yes"; name the candidates considered in any "no". Silent answers collapse this skill into ceremony.

1. **Shared root cause?** Do two or more items bottom out in the same `file:symbol`, or violate the same invariant?
2. **Shared touch site?** Do two or more proposed minimal patches modify the same file, function, or call site?
3. **Layer subsumption?** Is there a higher layer -- caller, owner, validator, type, contract, schema, lifecycle hook -- where one change makes >=2 downstream patches unnecessary? Or a smaller state model, where the mechanism stops on the hard case and names it instead of handling it? If yes, that wins.
4. **Redundancy after canonicalization?** After picking the upstream-most fix per cluster, are any per-item patches now no-ops? Drop them.

## Recurrence

A recurrence means reviewers are sampling one mechanism's invariants one per pass, and the next guard only waits for the next finding. Before choosing a locus, load **zoom-out** on the mechanism and every validator it must satisfy, list all of its invariants (not only the ones reviewers hit), and **step-through** each intermediate state, rollback included. Prefer the reframe that makes the failing states unrepresentable. Record the prior fix SHAs and the enumerated invariants in the locus's approach block.

## Fix-locus map

| Locus | File:symbol or layer | Items addressed | Single change |
|-------|----------------------|-----------------|---------------|
| L1    | <file:symbol>        | #1, #3, #5      | <one line>    |
| L2    | <file:symbol>        | #2              | <one line>    |

**Loci <= items**, often fewer, never more.

## Caller contract

- Per-item triage cites locus IDs -- it does not redesign fixes.
- Approach blocks are **per locus, not per item**, even when the caller's existing format says otherwise.
- Minimality is defined relative to the locus.
- Hedging-forbidden / demote-to-Investigate / alternatives-required rules apply at the locus level: a hedged locus demotes to `Investigate`, taking every item it would have addressed with it.

## Failure modes

- **Locus inflation**: every item gets its own one-row locus, skipping the audit. The most common silent failure -- name the alternatives considered when answering "no" to all four questions.
- **Locus deflation**: forcing unrelated items into one locus because aggregation looks tidy. The audit is descriptive, not prescriptive -- find shared structure, never invent it.
- **Pass-scoped audit**: treating each review pass as a fresh single-candidate case. Thirteen locally minimal fixes once landed on one prompt-builder function this way, each guarding one more backend rule, until a zoom-out deleted the case they all guarded.
- **Hedged layer choice**: "might lift this to..." in question 3 means you read intuition, not source. Re-do against actual upstream code.
