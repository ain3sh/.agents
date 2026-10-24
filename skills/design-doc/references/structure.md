# Structure: modes, facts, fill order, and content passes

## Frame before HTML

Pick the mode first. Do not force the RFC scaffold onto a memo or a report; a
selling document should not read like a budget request, research diary, or
roadmap.

| Mode | Spine |
|---|---|
| RFC / proposal | headline → context (primer first) → goals / non-goals → proposal → decision cards → tradeoffs → rollout → open questions |
| Technical memo / internal sell | metrics → headline → findings → demand → structural constraint → evidence → shipped artifact → limits → deployment. Charts and tables, not decision-card boilerplate |
| Sync prep | decision needed → evidence → options → recommendation → unresolved questions |
| Report / retrospective | the markdown source's own order, rendered by `build-md.js`; curate a front with `--front` ([report mode](report-mode.md)) |

Name three things before writing:

- **The single structural claim**: one sentence, ≤25 words. It becomes the
  `.lede` and the bold sentence of the `.headline`.
- **The 3–8 proof points or decisions**: decision cards in RFC mode; findings,
  comparisons, or deployment implications in memo mode.
- **The non-goals or current limits**: short, and one of them becomes the
  `.limit` finding.

**Title, lede, and nav must tell the story in order.** Read the `<h1>`, the
lede, and the top-bar nav labels in sequence: they must form one spine a
stranger can follow (principle → mechanism → measurement → merge → product →
proof bar → open questions). If they read as a topic pile, restructure sections
before polishing prose, or the review comes back "doesn't tell a coherent,
linear story."

## Source-of-truth pass

For every constant, file path, signature, enum, and limit you will cite, run
`rg` and write the verified fact to a scratchpad. Two failures this catches:

- **Invented limits.** One doc cited `LOOP_MIN_INTERVAL_MS`; it did not exist.
  The real guard was `intervalMs < MINUTE_MS` inline.
- **Caps with several terms.** "Jitter capped at 10%" was really "10% of
  period, capped at 15min."

When the PR description disagrees with the code, the code wins and you flag the
discrepancy. In report mode the source document is the truth for its own
numbers: copy them, and flag (do not fix) any that contradict each other.

## Fill the template top-down

`cp ~/.agents/skills/design-doc/references/template.html <dir>/<slug>.html`
and render it once with `screenshot.js --sample` to confirm it loads before
filling. Delete every block that is genuinely empty for this change; never pad,
and never leave TODO markers.

1. **`<title>` and top-bar nav**: one `<a href="#id">` per section, short
   labels (one or two words). Keep it to about eight links; merge sections
   rather than crowding the bar.
2. **Hero**: eyebrow (`.live` dot, then `kind // area // updated date`), `h1`,
   `.lede` (the claim for a zero-context reader; `data-typed` types it in, delete
   the attribute for a static line), `.linkline` (only links that earn the slot:
   tracker ticket, PRs). A conceptual title ("Where judgment sits") wins the
   argument but fails search and Slack recall: keep it and add
   `<span class="subtitle">` with the literal subject, then make sure the lede
   does not repeat the subtitle. Add `.metrics` only when four numbers carry the
   thesis. Add the `.chat` button only on a conjure-hosted page (it copies a
   prompt with the live URL).
3. **`.headline`**: the bottom line. Bold sentence = the answer in plain words;
   then the evidence with verbatim numbers and what it costs; `.hnote` = the
   caveat a careful reader raises first. Status and the review-by date go in its
   `.lhead`.
4. **Optional `.entries#updates`** on a living doc: newest first, `li.now`
   marks the latest.
5. **Context**: reader primer first, then what breaks today; every motivating
   ticket as an `.entries` row (`ID` in the key column, symptom as the title,
   2–3 sentences of failure and mechanism); then why now.
6. **Goals**: `.two-col` with a `.panel` of goals and a `.panel.limit` of
   non-goals.
7. **Proposal**: a `.headline` stating the mental model (≤25 words, one or two
   components in `code`), a show-me view when 3+ actors or states are involved,
   the prose the view does not replace, and the disposition table when an old
   system is displaced.
8. **Decisions**: `article.decision` × N, usually 60–70% of an RFC by length.
   All four `dt` slots (Decision, Rationale, Alternatives rejected,
   Consequence). No intro paragraph.
9. **Tradeoffs**: a table or short prose, where the decisions need it.
10. **Evidence**: `.findings` (each links to the table or chart that proves it)
    above the tables, charts, and bars. See [components](components.md#progressive-disclosure).
11. **Rollout**: `.stages` with status pills, a `.timeline` (flag posture,
    telemetry, the exact rollback), code with the changed line highlighted.
12. **Open questions**: `ol.numbered`, ordered by how much each answer would
    change the design, highest first.
13. **Optional `.chapters > details.chap`**: rounds, raw tables, and notes a
    reviewer may want but should not scroll past, one collapsed chapter each.
14. **`footer.doc`**: provenance only (PR · ticket · HEAD sha · source file ·
    build date). No colophon, reviewer roster, or typographic credits; they read
    as flourish and get cut in review.

Optional `figure.demo` for a demo video sits after the headline; follow
[show-me's asset embedding](../../show-me/references/surfaces.md#reusing-and-embedding-assets)
for source access and playback.

Memo mode keeps the same components and loop but swaps the goals/decision-card
spine for its own; remove unused template sections. Report mode: hand-write
only the hero fragment, the optional `--front`, and the footer.

## Zero-context rules

Review-tested: violating these draws "hard to read, context implicit and out of
order."

- **The lede is 1–2 sentences a new reader understands**: the user-visible
  problem, then the fix, in plain words. No vocabulary that only makes sense
  after the proposal ("separate liveness from commit" reads as meaningless), and
  never open on a non-goal ("the visual shape is unchanged"), which buries the
  why.
- **Context opens with a primer**: define the system being changed, its
  load-bearing primitives, and the terms the doc leans on ("monotonic",
  "idempotent") as they apply here. Goals must read cleanly using only words the
  primer introduced.
- **Spell out every motivating ticket in the page.** A bare tracker link is not
  context; the reader must never open Linear to follow the argument.
- **Order is how a stranger builds context**: problem → primer → mechanism of
  failure → concrete failures → goals → proposal.
- **Revising after review is a controlled change**: touch only the sections the
  feedback targets.

## Disposition table

When the proposal displaces an existing system, add a table with one row per
function the old system performs: the function, its fate with the verdict bolded
first (**Kept at full rigor** / **Kept as input, transformed on output** /
**Retired** / **Subsumed by X** / **Kept unchanged**), and a Where column
pointing at the owning section or decision. The people who built the old system
read the doc looking for exactly this table; without it the review comes back
"unclear what the hell happens to X."

## Inserting a block has knock-on edits

A new summary layer makes its neighbours redundant. Sweep these before
re-publishing, or the page says everything twice:

- **The lede.** Once a block carries the artifact spec, the lede should lead
  with the capability. Two adjacent blocks opening on the same fact is the most
  common duplication.
- **The section that first made the point.** A closing ask that restates the
  headline should read as follow-through, not first mention.
- **Staggered `nth-child` animation delays** (`.findings .rv:nth-child(n)`): a
  new child otherwise animates out of sequence.
- **Nav links**: a new or renamed section needs its `nav a` and `id`.
- **Old vocabulary after a rename.** `rg` the whole page for the old word; it
  hides in YAML samples, table rows, callouts, and open questions.

## Content passes

Run after the layout is clean. In report mode these apply only to text you
wrote; problems in the source go back to its author as flags.

- **Pass 1, structural cuts.** If a fact appears in the headline and in a
  decision, keep the canonical home and link to it ("full list: D7"). The page
  gets shorter. Cut template furniture: section meta-intros ("Eight decisions
  carry this PR…", "Each row is independently checkable."), navigational
  sentences ("§4 breaks the diff into…"; the nav is the map), and audience
  lead-ins ("A primer for readers outside the SDK effort."). Never put the same
  enumeration in Goals and Decisions; pick one home and point to it.
- **Pass 1.5, legibility.** No viewport may be an unbroken wall of text. Split
  by the seam, never by uniform bulletizing (which flattens an argument into a
  listicle): enumeration seam → bold-led bullets; contrast seam → split at the
  but/whereas pivot; coda → isolate the one-sentence conclusion.
- **Pass 2, polish.** Read aloud. Replace coinages ("due-times" → "a task that
  came due three times"), kill "actually", strip "we can", tighten
  cross-references. Edits remove or replace text; they rarely add.
- **Pass 2.5, voice.** Load **voice** for a quick independent sweep for slop,
  false agency, and filler. Keep it surgical.
- **Pass 3, visual explanations.** Apply **show-me** to structural or
  quantitative questions still buried in prose, using the facts from the
  source-of-truth pass and this template's components. Place each view where
  its question arises and cut the prose it replaces, keeping rationale and
  caveats. A diagram and its code companion are one explanation. When the
  question is how a mechanism works and a reader would learn by moving it,
  build an **animate-process** figure instead and embed its fragment.

## Traps

- ⚠️ **Decision cards that mint product surface.** New verbs, flags, config
  axes, parallel stores, and named presets reliably draw "this is ugly"; one
  session took three review rounds, each a level deeper (CLI flags → a dual
  dossier store → presets over existing settings). Audit each card for the
  smallest vocabulary that still composes into the feature set: composition of
  existing primitives before any new surface. When the design adds no surface,
  say so; "the primitive already ships" is the strongest selling line.
- ⚠️ **Answering "make it punchier" by trimming sentences.** Shorter paragraphs
  are still paragraphs. Change the structure: claim, scannable rows, one caveat
  ([progressive disclosure](components.md#progressive-disclosure)).
  Restructuring cut one doc's body copy ~60% and its callout height from 393px
  to ~280px; word-level trimming would not have.

## Citing code

`<code>name</code>` for functions and components inline. Each file path gets
one explicit anchor at the point of citation: "(see
`apps/cli/src/services/scheduled-tasks/loopSchedule.ts:42`)". Reviewers `rg`
from names; they do not click.
