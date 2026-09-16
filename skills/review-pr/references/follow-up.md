# Follow-up (re-review)

The author re-requested review, or new commits landed after our verdict. **Delta-first with a bounded interaction perimeter** — not a checkbox pass over our old findings, and not a rerun of the whole original review.

Start from the **dossier** (`dossier.md`), not the original review transcript; continue appending to the existing `review.notes.md` (same log across passes — query it by `F<id>` when a prior finding's history matters). If no dossier exists, reconstruct the minimum from our GitHub review threads (reviewed SHA from the review's commit anchor, findings from the threads), note the gap, and scaffold the ledger pair before proceeding.

## 1. Establish the delta

Fetch current head, conversation, CI state, and our prior threads. Identify:

- previously reviewed head SHA (from dossier) vs current head SHA;
- commits since, classified: **author responses** to our findings / **independent changes** (new features, fixes) / **base movement** (merges, rebases) / cleanup;
- files and contracts changed since the reviewed head (`git diff <prev-head>..<head> --stat`);
- whether prior diff anchors still apply (force-push detection: is `<prev-head>` still an ancestor of `<head>`?);
- whether the **body or its evidence** changed. Body: compare the raw-body fingerprint (and timestamp) with the dossier's `body_seen`. Evidence: an unchanged body and head prove nothing about a cited artifact — re-observe each one recorded under the dossier's *Description audit* (same identity; is it still reachable, still showing what was recorded?) and treat any difference as a delta. A body-only or evidence-only delta with an unchanged head is real — refresh the description audit (first-pass §1 and *Description claims*) against the current head: re-verify the touched claims, close prior description findings at mechanism depth like any other, and update `body_seen`/`audited_body`/`evidence`. A head change alone also re-opens commit-anchored claims per pr-description's staleness rules;
- which **acceptance scenarios** (dossier *Acceptance*, rules in `acceptance.md`) the delta affects: prior scenarios whose exercised surface, entry, transitions, platform, or premises changed are rerun on the new target; behavior, transitions, or platform support the delta newly touches get scenarios selected as first-pass would; the rest stand on their recorded evidence. A body- or evidence-only delta reruns nothing on the application while the recorded acceptance evidence remains valid for the unchanged head.

## 2. Whole-review escalation check

Escalate to a fresh **first-pass** (same session, note why) only if:

- reviewed history was force-pushed away and commits can't be mapped;
- the PR was substantially rewritten or the fix moved to another architectural layer;
- the base moved in a materially conflicting area;
- the original root-cause/invariant model no longer holds;
- the delta is too broad to isolate safely;
- our prior verdict was a `revise` at the architecture gate **and** the delta changes the ruling's premises — source changed at or around the ruled region, or new evidence contradicts a fact the ruling cited. The new head gets a fresh gate (`architecture-gate.md`, via first-pass §3) and, on `continue`, first-pass depth over everything the dossier's *Architecture gate* section lists as unreviewed; nothing below a `revise` was ever verified-safe, so Lane 3's perimeter does not shelter it.

A body- or evidence-only delta after a `revise`, with source and premises unchanged, is not an escalation: audit that delta (§1), retain the structural ruling and the dossier's unreviewed list verbatim, and reissue the verdict on that basis. Whenever a later pass does rule `continue`, every never-reviewed region still gets first-pass depth.

Otherwise proceed with the three lanes. "The author changed a lot of files responding to us" is normal follow-up load, not an escalation trigger.

## 3. Three lanes

### Lane 1 — Prior-finding verification

For each dossier finding, verify the response **at mechanism depth**:

- did the change land at the owning locus, or move the symptom elsewhere?
- does the intended invariant now hold? Trace it, don't take the reply's word.
- where tests were added/changed to close a finding, confirm they fail against the previously reviewed source for the stated reason (not an import/compile error) and pass on the new head — comparisons run on parent-arranged disposable snapshots per `worker-contracts.md`, never revert/restore inside the live checkout.
- classify: **resolved / unresolved / partially resolved / superseded / no longer applicable**.

An author reply of "fixed" with a commit that doesn't establish the invariant is an unresolved finding — say so plainly.

### Lane 2 — Independent delta review

Review every author-introduced change since the reviewed head **on its own merits**, exactly as first-pass would: fresh correctness defects, regressions introduced while addressing feedback, architecture/ownership changes, security/trust-boundary effects, convention violations, structural complexity, weakened or misleading tests. Do not assume a changed line is correct merely because it responds to us. New CI failures get full first-pass triage (flake / unrelated / real).

### Lane 3 — Interaction perimeter

Reinspect **unchanged** code only where the delta changes: a contract or schema; state transitions; lifecycle/concurrency; call paths; ownership boundaries; persisted data; dependency behavior; or an assumption the original review relied on. Trace those affected paths end to end. Do not re-review unchanged code outside this perimeter — the dossier's verified-safe list stands unless the delta touches its invariants.

## 4. Workers

Acceptance scenarios identified in §1 (reruns and newly required) are standing dispatches: they go straight through `acceptance.md` — same target, controller, admission, and state rules — with no hypothesis invented for them. For **investigation workers**, build a **delta suspicion ledger** (same shape as overcoverage §1, entries into the notes as `candidate`s) before any such dispatch. One worker per distinct unresolved proposition; pair static/probe modalities per `overcoverage.md` §2 only for material uncertainty; same reconciliation, notes-before-next-return, and third-worker admission rules. Typical follow-ups need zero to two workers — the lanes are mostly main-reviewer work. Lane 1 resolutions are notes entries too (`confirm`/`kill` against the prior `F<id>`s).

## 5. Verdict and close

Present to the user at the approval gate, sections kept separate (this is the gate presentation — the posted verdict body stays short per first-pass §6):

- prior findings: resolved / unresolved / superseded (with mechanism-depth evidence for contested ones);
- fresh delta findings;
- interaction-regression findings;
- suspicions killed during this pass;
- unrelated pre-existing defects (→ tickets, not verdict; a required acceptance scenario `failed` with pre-existing attribution keeps its state in the verdict as a completeness limit, per first-pass §6);
- current `APPROVE` / `COMMENT` rationale.

Then the standard first-pass **approval gate** and verdict-body rules apply (§6 of `first-pass.md`) — read that section; "never restate the threads" and requirements-stated-flatly bind here too. On approval: hand off to `/post-review`, append the `post` notes entry, and update the dossier per `dossier.md` (replace state sections, append history line).
