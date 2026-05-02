---
name: patch-coherence
description: Audit >=2 candidate fixes for shared root causes, shared touch sites, layer subsumption, and redundancy before per-fix recommendations are committed. Use when a workflow has produced multiple RCAs or fix proposals (e.g., several reviewer threads, multiple bugs in one ticket). Background knowledge for workflow commands -- not invoked directly.
---

# Patch Coherence

Run when a workflow has produced **>=2 RCAs or fix proposals** and is about to write each into its own recommendation block (e.g., `/address-review` after step-3 per-thread RCAs, `/implement` on a ticket with >=2 distinct bugs). Skip with one fix candidate.

Per-item RCAs compound badly: five reviewer comments produce five locally-minimal patches that may share a root cause, touch the same module five different ways, or all collapse into one upstream change -- the fix lands at five wrong layers instead of one right one. The audit must run **before** per-item recommendations are committed; post-hoc reflection rubber-stamps already-written blocks.

## The four-question audit

Answer all four explicitly. Name the items in any "yes"; name the candidates considered in any "no". Silent answers collapse this skill into ceremony.

1. **Shared root cause?** Do two or more items bottom out in the same `file:symbol`, or violate the same invariant?
2. **Shared touch site?** Do two or more proposed minimal patches modify the same file, function, or call site?
3. **Layer subsumption?** Is there a higher layer -- caller, owner, validator, type, contract, schema, lifecycle hook -- where one change makes >=2 downstream patches unnecessary? If yes, that layer wins.
4. **Redundancy after canonicalization?** After picking the upstream-most fix per cluster, are any per-item patches now no-ops? Drop them.

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
- **Hedged layer choice**: "might lift this to..." in question 3 means you read intuition, not source. Re-do against actual upstream code.
