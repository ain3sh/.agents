# Follow-up (re-review)

The author re-requested review, or new commits landed after our verdict. **Delta-first with a bounded interaction perimeter** — not a checkbox pass over our old findings, and not a rerun of the whole original review.

Start from the **dossier** (`dossier.md`), not the original review transcript. If no dossier exists, reconstruct the minimum from our GitHub review threads (reviewed SHA from the review's commit anchor, findings from the threads) and note the gap.

## 1. Establish the delta

Fetch current head, conversation, CI state, and our prior threads. Identify:

- previously reviewed head SHA (from dossier) vs current head SHA;
- commits since, classified: **author responses** to our findings / **independent changes** (new features, fixes) / **base movement** (merges, rebases) / cleanup;
- files and contracts changed since the reviewed head (`git diff <prev-head>..<head> --stat`);
- whether prior diff anchors still apply (force-push detection: is `<prev-head>` still an ancestor of `<head>`?).

## 2. Whole-review escalation check

Escalate to a fresh **first-pass** (same session, note why) only if:

- reviewed history was force-pushed away and commits can't be mapped;
- the PR was substantially rewritten or the fix moved to another architectural layer;
- the base moved in a materially conflicting area;
- the original root-cause/invariant model no longer holds;
- the delta is too broad to isolate safely.

Otherwise proceed with the three lanes. "The author changed a lot of files responding to us" is normal follow-up load, not an escalation trigger.

## 3. Three lanes

### Lane 1 — Prior-finding verification

For each dossier finding, verify the response **at mechanism depth**:

- did the change land at the owning locus, or move the symptom elsewhere?
- does the intended invariant now hold? Trace it, don't take the reply's word.
- where tests were added/changed to close a finding, confirm they fail against the previously reviewed source for the stated reason and pass on the new head (same revert/restore mechanics as first-pass §3).
- classify: **resolved / unresolved / partially resolved / superseded / no longer applicable**.

An author reply of "fixed" with a commit that doesn't establish the invariant is an unresolved finding — say so plainly.

### Lane 2 — Independent delta review

Review every author-introduced change since the reviewed head **on its own merits**, exactly as first-pass would: fresh correctness defects, regressions introduced while addressing feedback, architecture/ownership changes, security/trust-boundary effects, convention violations, structural complexity, weakened or misleading tests. Do not assume a changed line is correct merely because it responds to us. New CI failures get full first-pass triage (flake / unrelated / real).

### Lane 3 — Interaction perimeter

Reinspect **unchanged** code only where the delta changes: a contract or schema; state transitions; lifecycle/concurrency; call paths; ownership boundaries; persisted data; dependency behavior; or an assumption the original review relied on. Trace those affected paths end to end. Do not re-review unchanged code outside this perimeter — the dossier's verified-safe list stands unless the delta touches its invariants.

## 4. Workers

Build a **delta suspicion ledger** (same shape as overcoverage §1) before any dispatch. One worker per distinct unresolved proposition; pair static/probe modalities per `overcoverage.md` §2 only for material uncertainty; same reconciliation and third-worker admission rules. Typical follow-ups need zero to two workers — the lanes are mostly main-reviewer work.

## 5. Verdict and close

Present to the user at the approval gate, sections kept separate (this is the gate presentation — the posted verdict body stays short per first-pass §6):

- prior findings: resolved / unresolved / superseded (with mechanism-depth evidence for contested ones);
- fresh delta findings;
- interaction-regression findings;
- suspicions killed during this pass;
- pre-existing observations (→ tickets, not verdict);
- current `APPROVE` / `COMMENT` rationale.

Then the standard first-pass **approval gate** and verdict-body rules apply (§6 of `first-pass.md`) — read that section; "never restate the threads" and requirements-stated-flatly bind here too. On approval: hand off to `/post-review`, and update the dossier per `dossier.md` (replace state sections, append history line).
