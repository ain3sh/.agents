# Ground-up review (`ground-up`)

For complex PRs on core systems, where the PR's own design is the main risk. First-pass judges a PR against the code around it and the shape the PR already chose. Ground-up judges it against the best solution to the PR's real problem: designed first, by workers who never see the PR, then used as the yardstick for a full first pass and a `deeper` wave. The deliverable is the standard verdict plus the **delta** between the PR and that reference design, however large.

Entry: the `ground-up` keyword, or the user's yes to first-pass §1's recommendation. A follow-up on a ground-up review stays a follow-up; it inherits the dossier's *Reference design* through `lenses/architecture.md` §5.

The guards elsewhere in this skill (the gate's `revise` threshold, "taste is insufficient", no worker without a named hypothesis) exist because "I'd have built it differently" is usually taste. This workflow does not drop them; it earns past them with evidence. Independent designers who never saw the PR converging on a decision the PR breaks is evidence, not taste.

## 1. Crux, before the diff

Scaffold the ledger pair (`systems/dossier.md`, `mode: ground-up`). Fetch PR metadata, the linked ticket or issue, and `gh pr diff --name-only` through **pr-context**. Do not read the diff, the branch, or the design sections of the PR body yet: a PR body usually describes its solution, so take only the problem from it. Arriving from first-pass after reading the diff, write the brief anyway and lean harder on §2; the reference design comes from the blind workers, and you only synthesize it.

Run `lenses/crux.md` steps 1–2 on the base revision: the map, then the **crux brief**. Record the brief, and how the review got here (the `ground-up` keyword or a yes to first-pass's complexity check), as a `gate` notes entry; the brief also goes in the dossier's *Reference design* section.

## 2. Blind phase

Standing dispatches (`systems/workers.md`), all heavy and read-only, on a parent-arranged snapshot at the base SHA. **Blindness:** a blind worker receives the crux brief, the snapshot, and `lenses/crux.md`, never the diff, PR number, branch, body, or the author's framing, and its prompt tells it not to look the PR up. Unavailable subagent type → report a specialist blocker; never downgrade silently.

- **Prior-art research** (`subagent_type: sol`; split by axis when the space is broad, such as production systems versus published work and open source): how the strongest systems and teams solve this crux, which approaches hold up and which fail and why, and the trade-offs that decide between them. Uses web research tools (WebSearch, FetchUrl), plus the `paper-search` MCP tools when connected and the field has literature. Returns approaches with a source per claim, what each optimizes, its failure modes, and which brief constraints it fits or breaks; an unsourced claim is marked as recall.
- **Independent designs**, dispatched once research returns, each given the brief and the research digest. At least two designers on different models (`fable`, `opus`); add `sol` when the crux spans several subsystems. Each loads `lenses/crux.md` (which brings in **zoom-out** and **patch-coherence**) and **show-me**, then builds what it would ship in this codebase by `lenses/crux.md` steps 3–5, from base source, and returns its **layer ledger** plus: owners and boundaries; state model and contracts as types and signatures; data and control flow as **show-me** views; each key decision with the rejected alternative and why; the failure modes it handles; build and migration cost. Every layer and decision cites the base source or research it rests on.

Scale with the problem: a crux with independent sub-problems gets a research axis and a designer pair per sub-problem. Record each dispatch as a `dispatch` notes entry and each return as a `reconcile` entry.

## 3. Reference design

Admit each return whole: a decision traceable to neither base source nor a cited source counts as recall, not evidence. Then compare the designs' layer ledgers, pure cores first, then layer by layer:

- **Convergent:** designers agreed independently. Essential; record who agreed and on what evidence.
- **Divergent:** record each option and its trade-off. Research or a hard constraint may settle it (record that evidence); otherwise it stays open, which makes it taste.

Write the **reference design** as one merged layer ledger: the shared pure core, convergent layers, settled and open divergences, sources, and one **show-me** view of its shape. Record it as a `gate` notes entry and in the dossier. It is fixed before you read the diff: changing it afterward needs a source fact the brief missed, recorded as another `gate` entry, never the PR's own design.

## 4. First pass against the reference design

Now read the PR. Run `workflows/first-pass.md` §1–§5 in full, minus two §1 steps this workflow's §1 already did (the complexity check and the ledger scaffold), with three differences:

- The architecture gate sets the PR against the reference design (`lenses/architecture.md` §5).
- A `revise` ruling does not stop the pass, and first-pass's clauses written for a ruling that does stop it don't apply. The delta needs the whole PR, so §3–§4 and the structural sweep run in full anyway, and §5 records the coverage actually reached: no *Unreviewed* list, and a *Verified-safe* list of what was verified. A finding the reference direction would subsume says so.
- Record the **delta**: for every reference decision, the PR's choice is *matches*, *differs*, or *missing*. Each difference is a finding (`F<id>`), tiered per `lenses/architecture.md` §5. Then run `lenses/crux.md` §5's complexity accounting of the PR against the reference ledger: each PR mechanism traces to a row or is accidental complexity.

## 5. Deeper, by default

Run `workflows/deeper.md` right after §4, without asking for a go-ahead and whatever the gate ruled: invoking ground-up is the explicit request its precondition names. Its categories also cover deltas whose cost or reachability is unsettled (does the PR's choice actually fail where the designs say it will?). The qualification bar still binds.

## 6. Summary and gate

Produce first-pass §5's review-state summary, plus:

```text
Reference design: <crux; convergent decisions; settled and open divergences; sources>
Delta:
- <decision>: reference <choice> | PR <choice | missing> — <evidence: designers agreeing, sources> — F<id>
Untraced PR mechanisms:
- <mechanism, file:line>: no ledger row — F<id>
```

Then first-pass §6's approval gate and verdict. The verdict's **Architecture** section leads with the delta, and its view sets the PR's shape beside the reference design.
