# Overcoverage (`deeper`)

An adversarial second wave with two objectives, run from a completed first pass (review-state summary in-context — or seeded from the dossier per SKILL.md routing; `worker-contracts.md` loaded):

- **A. Adjudicate** every unresolved suspicion from the review-state summary — workers exist to prove findings real *or* kill them as false positives, red herrings, or pre-existing behavior.
- **B. Expand** into high-risk changed surfaces the first pass did not deeply cover.

It is **not** a generic duplicate scan. Completed first-pass axes (conventions, structural sweep, slop scan, CI triage, repro) stay closed unless new evidence reopens them.

## 1. Build the category ledger

Group remaining work into the **smallest coherent technical categories**. A category qualifies only if it contains a concrete unresolved suspicion, or a high-risk changed surface without deep coverage. Do not invent categories to raise worker count; broad labels ("holistic", "blast radius") that overlap the whole diff are not categories.

For each qualifying category, write down before dispatch:

```text
Category: <smallest coherent surface, e.g. "fork-cut boundary contract">
Suspicions:
- <precise hypothesis / failure scenario>
Path: <producer → transform → consumer>
Evidence so far: <what first pass established>
Remaining uncertainty: <the exact open question>
Impact if real: <user-visible consequence>
Files/tests: <bounded list>
```

Show the ledger to the user with your proposed pairings before dispatching if the wave is large (>3 categories); otherwise proceed.

## 2. Paired dispatch — differ by method, not conclusion

For each material category, dispatch a pair whose members use **different evidence modalities** on the **same suspicions**:

1. **Medium static auditor** (read-only): trace the complete contract and every caller/consumer; inspect guards, invariants, schemas, tests, prior art; determine whether each suspicion is reachable, safe, pre-existing, or contradicted by the implementation; audit nearby static risks in the assigned surface.
2. **Heavy adversarial prober**: construct concrete edge cases for the same suspicions; execute focused probes where runtime evidence adds information (untracked probe files only, per the hygiene rules in `worker-contracts.md`); reason from source when the contract is already decisive — a probe is not mandatory; test nearby variants that could expose a different manifestation.

Both workers are **neutral investigators**: their job is to **CONFIRM OR KILL** each hypothesis — not to defend the main review, and not to prefer falsification. Use symmetric language in prompts ("prove or disprove", "confirm or kill", "determine exact behavior", "establish reachability"). Never instruct a worker to "try to disprove first" or to construct benign explanations before weighing evidence — directional effort wastes tokens and biases results.

Each worker prompt must contain: the category ledger entry verbatim (hypotheses, path, evidence, uncertainty), bounded file list, the output schema from `worker-contracts.md`, and probe/read-only hygiene rules. Workers must **not** rescan the whole PR.

Lightweight categories (one narrow suspicion, one file) get a single worker, not a pair — pairing is for material uncertainty where independent modalities genuinely de-correlate errors.

## 3. Reconcile per category — before any further dispatch

When a pair returns:

- Compare static vs executed evidence; where they disagree, the disagreement itself becomes the named open question.
- Remove false positives, red herrings, and pre-existing behavior (pre-existing issues route to tickets/conversation comments, not findings).
- Apply **patch-coherence** across surviving candidates: cluster by violated invariant and owning locus; collapse downstream manifestations into the upstream finding; merge duplicates.
- Record killed suspicions with the exact invariant/probe that killed them — these go in the dossier's verified-safe section and, where they contradict a headline concern, into the review narrative.
- State what, if anything, remains verdict-relevant and unresolved.

A category with no remaining named question is **closed**. Closed categories do not receive more workers.

## 4. Third-worker admission

Dispatch a third worker into a category **only** for a named reason:

- the pair disagrees on a verdict-relevant claim;
- evidence came back inconclusive, or a probe was unfaithful to the real path;
- the pair exposed a new high-impact subsystem outside the original bounds;
- one exact verdict-relevant question remains that neither modality settled.

The third worker receives the prior results and the exact remaining question — never "review this category again from scratch." Not sufficient reasons: "important category", "maybe another model finds more", "the pair found several things."

## 5. Merge into the review

Fold surviving findings into the first-pass finding set (voice severities, dedupe against existing findings), update the review-state summary (confirmed / verified-safe / coverage map), and return to the first-pass **approval gate** (§6 of `first-pass.md`) with the combined set. The dossier write on posting records the wave: categories, worker assignments, conclusions, killed suspicions.
