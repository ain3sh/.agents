# Analysis, title, and required body

Use this workflow for every new or rewritten PR description. `What / Why / How`
is the canonical Description grammar; later sections own detail, not the first
mention of a fact that changes the merge decision.

## Pre-flight

Emit this checklist and tick it as you work:

```text
pr-description checklist:
- [ ] Diff analyzed three-dot; what/type/scope/why extracted
- [ ] Strongest evidence and material merge cost identified
- [ ] Title: outcome/invariant first, type(scope), imperative, <=72 chars
- [ ] First screen passes the four-question skim gate
- [ ] Five required sections present; conditional catalog walked row by row
- [ ] Structural change? Architecture diagram drawn (artifacts.md)
- [ ] Concrete visual change? Live proof attached high in body (visual-evidence.md)
- [ ] Verification outcome-first; CI compressed to one line
- [ ] Body length scales with complexity, not effort
- [ ] Body composed with a file tool and applied through REST (publish.md)
- [ ] Refresh only: base resolved and marker re-stamped (refresh.md)
```

## Analyze the diff

Run the entrypoint's Detect commands. Three-dot diffs match GitHub's Files
changed tab from the merge base; two-dot logs select commits in HEAD but not
base.

- Extract **what** changed, **type**, **scope**, and **why**.
- Identify the strongest evidence that the change works and any risk, migration,
  compatibility consequence, or review cost that could change the merge
  decision.

## Title

Format: `type(scope): imperative description`, at most 72 characters.

Choose the highest stable abstraction the diff and evidence prove:

1. user or operator outcome
2. product capability or observable behavior
3. safety, reliability, or architectural invariant
4. implementation mechanism

Use the mechanism when it is the durable value of the PR. Include a magnitude
only when it is verified, representative, materially distinguishes the change,
and still fits the length limit. Use declared repository scopes; comma-separate
multiple scopes or broaden. On squash-merge repositories, treat the title as
the permanent commit subject.

## First-screen skim gate

Keep `What / Why / How`. Strengthen it with the best available evidence rather
than replacing it with a second schema. These are the questions the Description
answers, not mandatory headings.

- **What**: observable outcome or capability delta. Make impact concrete.
- **Why**: stakes or first unintended side effect.
- **How**: new flow or invariant, not a file tour.

If a fact from Verification, Performance Evidence, Contract Delta, Migration,
or Risk materially changes the merge decision, preview it in the Description.
The later section still owns methodology and detail.

Read only the title and first screen. A reviewer must be able to answer:

1. Why merge this?
2. What changes?
3. Why believe it works?
4. What could it cost or break?

Use two to four short sentences plus one compact table or list when that scans
faster. The opening stands alone without the ticket. For a large structural PR,
use **Why** / **What this PR does** and a one-line **Net effect for users**.
Link a design document here when it carries the rationale. Keep anti-goals,
scope maps, detailed RCA, and file tours in their owning locations.
A small PR may omit **Why** when the cause is self-evident.

## Section catalog

The five required sections always fire. Conditional sections are a menu, not a
checklist. Omit headings whose trigger does not fire. The order below is render
order, not evidence priority: decision-relevant facts are previewed in the
Description.

| # | Section | Fires when |
|---|---|---|
| 1 | Description | always; inline anti-goals, scope map, design link, or RCA as needed |
| 2 | Visual Evidence | concrete UI/TUI/CLI/rendered-media change |
| 3 | Repro Recipe | new feature or fixed bug with a manual surface |
| 4 | Architecture | components, flows, boundaries, integrations, or module structure changed |
| 5 | Related Issue | always; add lineage/stack block when applicable |
| 6 | Reviewer Guide | always |
| 7 | Risk & Impact | always |
| 8 | Contract Delta | DB/API/wire/shared type touched |
| 9 | Migration & Rollout | flag, migration, environment, or breaking change |
| 10 | Performance Evidence | performance-sensitive change |
| 11 | Telemetry & Observability | metrics, logs, traces, alerts changed |
| 12 | Reverse Dependencies | changed surface has more than three consumers |
| 13 | Side Effects | acknowledged regression |
| 14 | Verification | always |
| 15 | Implementation map | large multi-subsystem diff, roughly 20+ files |
| 16 | Changes since last review | active-review refresh |
| 17 | Implementation Notes | matching `.agents/specs/*.notes.md` exists |

Conditional templates live in `conditional-sections.md`.

## Required sections

```markdown
## Description

**What**

<Observable outcome or capability delta. Preview decisive evidence here.>

**Why**

<Stakes or first unintended side effect.>

**How**

<New flow or invariant in one or two sentences.>

## Related Issue

Closes TEAM-123

## Reviewer Guide

**Diff shape:** <attention split; generated/noise files are "skip", never a %>
**Review depth:** Skim | Standard | Deep — <one-line reason>
**Read order:**
1. `path/to/entry.ts`: <one clause>
2. `path/to/next.ts`: <one clause>
3. Tests: <invariant they pin>

**Open for pushback:** <one live design call + code anchor; omit when none>

## Risk & Impact

<Specific risks and the concrete scenario in which each fires.>

## Verification

**Behavior verified @ `<sha>`:** <state → action → observation>
**Regression coverage:** <owning suite + invariant + failure mode>
**Not tested:** <real skips with one reason each; N/A only when true>
**Standard validators:** <one compressed line; include triaged unrelated failures>
```

### Reviewer Guide

Keep it scannable. Use one file or tight pair per numbered line and causal,
not alphabetical, order. Add deliberate behavior changes that could look like
merge noise. Drop an empty pushback prompt.

### Risk & Impact

Name scenarios, not categories. "Low risk — isolated" is valid only when true.
For higher risk, state how the diff contains it: tests, E2E matrix, no
persistence/protocol change, or single-revert restorability. Never claim a
flag, migration, or mitigation the diff does not contain. Put future rollout
intent in Migration & Rollout and label it as a plan.

### Verification

Lead with observed behavior, not validator inventory. Tie evidence to listed
risks. Use a before/after table for enumerable behavior and include unchanged
rows that show preserved contracts. Pin behavior claims with `verified @`.

Name the sentinel case that turns red on regression and why its layer owns the
invariant. CI status does not belong here; compress format/lint/type/test status
to one Standard validators line.

## Length and writing

Length scales with complexity, not effort. A small PR is roughly 150 words. A
complex PR earns length through triggered conditional sections. If always-on
prose exceeds roughly 450 words without conditional sections, trim the file
tour and diff narration.

Use plain language before symbols. Keep paragraphs under three sentences.
Use formatting only to clarify real information. Do not invent decorative
before/after claims, hide required context in `<details>`, or let prose terms
collide with existing product surfaces.

Present-tense, third-person voice: "This PR adds", not "I added". Date any
first-person note.

## Stable searchable markers

| Marker | Use when |
|---|---|
| `Constraint from:` | external requirement, e.g. `Constraint from: FAC-123 ("must work offline")` |
| `Decision-maker:` | named owner of a non-obvious call |
| `As of:` | architecture-blame snapshot of the touched module |
| `Sentinel test:` | canary that fails first, with path/line |
| `verified @` | commit that anchors a behavior claim |
