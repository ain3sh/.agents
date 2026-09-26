---
name: design-doc
description: Author a publication-grade single-file HTML design doc, technical memo, or rendered report/retrospective, plus 1600x900 Slack cards and a hero thumbnail. Factory visual system, adaptive RFC/memo/report structure, markdown-to-HTML builder, fact-checked references, light/dark Playwright verification, and secret-gist publishing.
---

A design doc here is one self-contained HTML file — fonts via Google Fonts, all styles inline, no JS framework — with the precision of an internal engineering artifact and the visual confidence of Factory product surfaces. The aesthetic exists to make reviewers actually read it; the structure exists to make the argument legible.

Output target: ~1.5k–3k lines, under ~1 MB (80–300 KB typical), prints to A4, dark-mode aware, publishable as a secret gist viewed via `gistpreview.github.io`. Shareable outputs next to it: a hero thumbnail and, when asked or when the argument has several beats, 1600×900 Slack cards ([share images](references/share-images.md)).

This skill owns the document's argument, scaffold, visual system, full-document
verification, and publishing. Load **show-me** for visual explanations: pass
the verified facts, reader question, and this template's components/tokens;
it owns representation, rendering, code companions, and asset embedding.

**Two rules outrank every visual rule below.**

1. **Numbers survive verbatim.** Every number, id, verdict, and claim in the doc, stat band, thumbnail, and cards matches its source character for character, with its block, ticket, or file. Re-derive nothing, round nothing differently, drop no hedge. When rendering an existing source (report mode), prose passes through unchanged too; only layout is added.
2. **Voice before polish.** Load **voice** for every fresh sentence (tagline, captions, card headings, callout claims): no slop, no false agency, no filler. A handsome doc with one inflated claim loses its most careful reader.

## When to use

- Engineer asks for an RFC, design doc, ADR, monograph, technical spec, or sync-prep brief.
- Engineer needs an internal technical memo that sells a shipped capability with evidence rather than proposal boilerplate.
- A retrospective, measurement report, or changes-and-impact memo exists in markdown and needs rendering as a shareable doc and cards ([report mode](references/report-mode.md)).
- A PR has architectural weight (≥2 reviewers, multiple sub-decisions) and needs framing beyond the PR description.
- A change touches a contract, persistence, or cross-component ownership and needs one shareable artifact.

**Skip this skill for** short READMEs, Linear ticket bodies, PR descriptions, slide decks, or anything best read in markdown — use markdown instead.

## Process recipe

The order matters. Skipping step 2 is the most common failure: prose ends up referencing constants or call sites that don't exist.

### 1. Frame the argument and choose the document mode

Choose the mode before touching HTML:

- **RFC / proposal:** problem → primer → goals/non-goals → proposal → decision cards → tradeoffs → rollout → open questions.
- **Technical memo / internal sell:** demand → structural constraint → evidence → shipped artifact → limits → deployment. Lead with a four-stat proof band plus the callout panels in [The "so what" layer](#the-so-what-layer), and use charts/tables instead of decision-card boilerplate.
- **Sync prep:** decision needed → evidence → options → recommendation → unresolved questions.
- **Report / retrospective:** the argument already exists as markdown (retro, findings, measurement report). TL;DR per goal → figures → changes-and-impact table (one row per change, `↓ = ↑ ·` goal glyphs) → numbered sections. Render it with `build-md.js`; prose passes through verbatim. Spine, glyph legend, and builder flags: [report mode](references/report-mode.md).

Do not force the RFC scaffold onto a memo or a report. A selling document should not read like a budget request, research diary, or next-cycle roadmap.

Name three things:
- **The single structural claim** — one sentence, ≤25 words. This becomes the tagline + §1 lede.
- **The 3–8 proof points or decisions** — decision cards in RFC mode; scorecards, comparisons, or deployment implications in memo mode.
- **The non-goals or current limits.** Keep them short and relevant to the chosen mode.

**The hero + TOC must tell the story in order.** Title, tagline, and section headings read in sequence must form one narrative spine a stranger can follow (e.g. one principle → mechanism → measurement → merge → product → proof bar → open questions). If the TOC reads as a topic pile, restructure sections before polishing prose — the review otherwise comes back "doesn't tell a coherent, linear story."

### 2. Source-of-truth pass

For every constant, file path, function signature, enum, and limit you intend to cite, run `rg` and verify. Write verified facts to a scratchpad. Two failure modes you will hit if you skip this:
- **Numeric limits.** Prior session caught `LOOP_MIN_INTERVAL_MS` referenced in prose — it didn't exist; the actual guard was `intervalMs < MINUTE_MS` inline.
- **Caps with multiple terms.** Prior session caught "jitter capped at 10%" that should have been "10% of period, capped at 15min."

When the PR description disagrees with the code, **the code wins** and you flag the discrepancy to the user. In report mode the source document is the truth for its own numbers: copy them, and flag (do not fix) any that contradict each other.

### 3. Start from the template or the builder

```bash
# RFC / memo / sync prep: fill the scaffold
cp ~/.agents/skills/design-doc/references/template.html <project>/.agents/specs/<slug>-design.html
# Report mode: render the markdown source on the same stylesheet
node ~/.agents/skills/design-doc/references/build-md.js <source.md> <out.html> --eyebrow="..." --hero=hero.html
```

Do not start from scratch, and do not write a second stylesheet: `build-md.js` reads `template.html`'s styles at build time. The styles encode hard-won decisions (Factory tokens, Geist hierarchy, `text-wrap: balance`, decision-card grid, auto-hide nav, dark/light modes, print stylesheet). The template is a working scaffold — render it once with the screenshot script in step 5 to confirm it loads before filling.

Before styling, search the repo for `DESIGN.md`, brand guidance, or live tokens. **The repo's design canon wins.** In Factory repos, read `packages/core-ui/src/DESIGN.md`; the bundled template follows that dark-first system.

### 4. Fill the scaffold top-down

For RFC mode, fill the scaffold top-down:

1. `<title>`, eyebrow, `h1.title`, `.tagline`, `.linkline`. The linkline is one borderless mono row for links that earn their slot (tracker project/ticket, PRs). Status, author, date, and reviewer rosters are fat — provenance lives in `footer.doc`. A conceptual title ("Where judgment sits") wins the argument but fails search and Slack recall; keep it and add `<span class="subtitle">` carrying the literal subject ("Converging Factory's PR review flows"), then sweep the tagline so it doesn't repeat the subtitle.
2. **Optional** `figure.demo` if there's a demo video; follow [show-me's asset embedding](../show-me/references/surfaces.md#reusing-and-embedding-assets) for source access and playback.
3. §1 Summary — `.lede` with `.dropcap` + 1 supporting paragraph (zero-context rules below).
4. §2 Context — reader primer first, then what breaks today (tickets spelled out), why now.
5. §3 Goals & non-goals — `.two-col > .panel`.
6. §4 Proposal — `.pullquote` thesis, a view from `show-me` when useful, and the prose that the view does not replace.
7. §5 Key decisions — `article.decision` × N. **Usually 60–70% of the doc by length.**
8. §6 Tradeoffs — `table.kv` or short prose.
9. §7 Rollout & verification — feature-flag posture, telemetry, rollback.
10. §8 Open questions — `ol.numbered`, **ordered by how much each answer would change the design** (highest leverage first).
11. `footer.doc` (provenance: PR, ticket, HEAD sha, file path). The template ships no colophon — typographic-credits sections read as flourish and get cut in review; don't add one unless asked.

Skip a section only if it's genuinely empty for this change — don't pad.

For memo mode, replace the goals/decision-card spine with the structure selected in step 1. Keep the same components and verification loop, but remove unused template furniture rather than leaving empty RFC sections.

For report mode, the source's sections are the spine. Hand-write only the `--hero` fragment (tagline quoted from the source, `.statband` with the final numbers, optional callout panels) and the footer provenance.

**Write for a reader with zero context (review-tested — violating these draws "hard to read, context implicit and out of order" feedback):**

- **§1 Summary lede = 1–2 sentences a completely new reader understands**: the user-visible problem in plain words, then the fix in plain words. No internal vocabulary that only makes sense after §4 ("separate liveness from commit"-style taglines read as meaningless), and never open with a non-goal ("the visual shape is unchanged") — it buries the why.
- **§2 Context opens with a basics primer** before any deep-dive: define the system being changed and its load-bearing primitives, and define terms the rest of the doc leans on ("monotonic", "idempotent", …) — what they mean *here* and why they matter. Goals/Non-goals must read cleanly using only words the primer introduced.
- **Spell out every motivating ticket in-doc**: bold `ID — symptom` title, then 2–3 sentences of user-visible failure + mechanism. A bare tracker link is not context; the reader must never need to open Linear to follow the argument.
- **Order = how a stranger builds context**: problem → primer → mechanism of failure → concrete failures → goals → proposal. When revising a published doc against reviewer feedback, keep it a controlled change — touch only the sections the feedback targets.
- **When the proposal displaces an existing system, add a function-by-function disposition table** (`table.kv`): one row per function the old system performs, verdict bolded first (**Kept at full rigor** / **Kept as input, transformed on output** / **Retired** / **Subsumed by X** / **Kept unchanged**), plus a Where column pointing at the owning section or decision. The people who built the old system read the doc looking for exactly this table; without it the review comes back "unclear what the hell happens to X."

**Inserting a block into a finished doc has knock-on edits.** Adding a summary layer makes neighbours redundant; sweep for these before re-publishing, or the doc reads as saying everything twice:

- **The tagline.** Once a new block carries the artifact spec, the tagline should lead with the capability instead. Two adjacent blocks opening on the same fact is the most common duplication.
- **The section that originally made the point.** A closing ask that now restates a fold-level callout should be reworded to read as follow-through, not first mention.
- **Staggered-animation `nth-child` rules**, if the container has them — a new child otherwise appears un-animated or out of sequence.
- **Old vocabulary after a rename.** When a concept is renamed or demoted mid-revision ("presets" → plain settings), `rg` the whole doc for the old word — it hides in YAML samples, table rows, callouts, and open questions, not just the section you rewrote.

### 5. Iteration loop (mandatory)

Write → capture → inspect → fix:

```bash
node ~/.agents/skills/design-doc/references/screenshot.js <abs-path-to-html>            # full sweep
# → /tmp/doc-previews/scroll-{light,dark}-NN.png, hero-dark-v2.png
node ~/.agents/skills/design-doc/references/screenshot.js <abs-path-to-html> --sample   # hero + one per component
# → /tmp/doc-previews/sample-{light,dark}-NN-<component>.png
```

Playwright must resolve. Every script (and `build-md.js` for `marked`) resolves modules through `references/lib.js`, which searches `PLAYWRIGHT_NODE_MODULES`, `NODE_PATH`, then every `node_modules` above your **CWD**; a bare `require('playwright')` would start from the script's directory instead. Run from inside (or under) a project that has Playwright, or set `PLAYWRIGHT_NODE_MODULES=/abs/path/to/node_modules`. If Chromium is missing: `npx playwright install chromium`. Last resort: `cd /tmp && npm i playwright && npx playwright install chromium`. The scripts work on any HTML page, not only the template's markup, and force `scroll-behavior: auto` so smooth scrolling cannot freeze every segment at the top.

**Which sweep, and how to read it.** A dark hero alone is never enough: charts, tables, diagrams, and callouts fail several viewports below it.

- **Full sweep, every segment, both schemes**: first render of a hand-authored doc, after any CSS or template edit, after adding a new component type or a `show-me` view, and once before sharing. Read the hero, tables, charts, diagrams, and code segments at `image_quality="high"`; prose-only segments can be read at default quality and re-read high only if something looks off.
- **`--sample` is sufficient** while iterating on content in a doc whose layout already passed a full sweep, and for builder output (`build-md.js`), where one stylesheet renders every instance of a component identically. Read every sample at high quality.

Fix layout, contrast, and overflow bugs visually before tightening prose. Bugs you will only catch this way:
- `dl > dd` falling under `dt` instead of into column 2 → the template pins `grid-column: 2`; if you copied a card and removed it, restore it.
- Dark-mode contrast failures on `--code-bg` and `--accent-soft`.
- Check embedded views against [show-me's render checks](../show-me/references/surfaces.md#browser) at the document's actual content width.
- **TOC rail clipping**: the collapsed `nav.toc` must fit its widest roman numeral — at 56px "VIII" clipped to "VII"; the template now ships 68px, which fits every four-character numeral (through XVII, so 17 sections). Recheck if you shrink the rail; past 17 sections, merge sections rather than widening it.

If layout is mysterious, run `inspect.js`:
```bash
node ~/.agents/skills/design-doc/references/inspect.js <abs-path> "<css-selector>"
```
It dumps bounding rects + computed styles for the first 12 matches.

### 6. Content passes

After visual layout is clean. In report mode these passes apply only to text you wrote (hero, captions you added, cards); the source's prose stays verbatim, and problems in it go back to its author as flags.

- **Pass 1 — structural cuts.** If a fact appears in §1 and §5, delete it from §1 and link forward ("full list: D7"). The doc gets *shorter* in this pass, not longer. **Cut template furniture** — scaffolding prose users reliably nuke as fat:
  - Section meta-intros that describe the section instead of adding content ("Eight decisions carry this PR…", "The parts where good engineers could disagree…", "Each row is independently checkable."). The heading already does that work; open on the first real item.
  - Navigational cross-reference sentences in §1 ("§4 breaks the diff into…; §5 defends…; §7 records…") — the TOC is the map.
  - Audience lead-ins ("A primer for readers outside the SDK effort.") — just start the primer.
- **Pass 1.5 — legibility.** No wall of text at any scroll-point: every viewport needs a structural break. Split with content-fitted patterns, never uniform bulletization (which flattens an argument into a listicle):
  - *enumeration seam* → bold-led bullets (`**Admission** — the checklist forces…`);
  - *contrast seam* → split the paragraph at the but/whereas pivot;
  - *coda* → isolate the one-sentence conclusion as its own paragraph.
- **Pass 2 — polish.** Read aloud (literally, your inner voice catches bumps). Replace neologisms ("due-times" → "task that came due three times"), kill "actually", strip "we can", tighten cross-references. Each edit should remove or replace text, rarely add.
- **Pass 2.5: voice sweep.** Load **voice** for a quick craft pass focused on anti-slop, false agency, and filler. Keep edits surgical and preference-light so this reads as an independent quality gate, not a rewrite.
- **Pass 3 — visual explanations.** Apply `show-me` to structural or quantitative
  questions still buried in prose, using the facts verified in step 2 and this
  document's components. Place each accepted view where its question arises;
  cut the prose it replaces, keeping rationale and caveats. A diagram and its
  code companion are one explanation, not two sections.

### 7. Re-verify

Re-run `screenshot.js`. **`scrollHeight` should drop, not grow** — prior session went 18820 → 18429 px and 17 → 14 segments with no information lost. The only sanctioned growth is Pass-3 diagrams; prose height still shrinks.

### 8. Share images and publish (optional)

Generate the hero thumbnail for any shared link, and Slack cards when requested or when the argument has more than one postable beat: [share images](references/share-images.md). Publish only on request: [publishing](references/publishing.md), size budget first.

## Aesthetic foundation

The bundled default follows Factory's visual system:

- **Dark-first:** black canvas, white foreground, warm gray support text. Light mode exists for marketing/install surfaces and print.
- **One accent:** Factory orange (`#EE6018`) marks active paths, key numerics, section metadata, and the primary comparison. It is not ambient decoration.
- **Flat surfaces:** no shadows, glows, gradients, glass, or elevation theater. Depth comes from surface contrast, 1px borders, spacing, and type.
- **Mono-led:** Geist Mono carries labels, metadata, code, chart axes, and diagram text. Geist carries headings and prose.
- **Restrained geometry:** 4px default radius, 6px only for large containers, pills only for actual tags.
- **Technical confidence:** left-align interiors, use generous outer margins, and let scale rather than bold weight carry hierarchy.

If the repo defines a different canon, adapt the tokens and typography to it. Do not invent an independent theme merely because the artifact is standalone.

## Typography craft

| Role | Factory treatment | Note |
|---|---|---|
| `body` | Geist 400, 18px, `line-height: 1.62`, `letter-spacing: -0.01em` | Larger, calmer body copy works better than compact editorial serif text for broad-team docs. |
| `h1.title` | Geist 300, 52–82px, `line-height: 0.98`, tracking `-0.045em` | Light weight plus scale creates authority without a marketing-heavy display face. |
| `.tagline` | Geist 400, 19–23px, muted foreground | Keep upright. No italic in Factory product or document surfaces. |
| `section.block > h3` | Geist 300, 32–44px, tracking `-0.035em` | Use type scale, not orange or bold weight, for section hierarchy. |
| `.dropcap` | Geist Mono 400, orange | A technical accent, not a decorative swash. Remove it if it feels literary rather than useful. |
| `.pullquote p` | Geist 300, 24–30px, upright, orange left rule | Treat it as an engineering assertion, not a quotation ornament. |
| All mono | Geist Mono 400, uppercase labels at `0.08em` | Use `font-feature-settings: "zero"` for numeric disambiguation. |

Use `text-wrap: balance` on headings, taglines, pullquotes, figcaptions, and decision titles. Use existing tokens and `color-mix(in oklab, …)` only for tonal versions of the canonical palette.

## Quantitative proof and charts

Put a **four-stat proof band** directly under the hero when four numbers carry
the thesis. Values use orange; labels and explanations stay neutral. The
shipped/recommended row gets the sole orange bar and a subtle orange-tinted
surface; incumbents, controls, and reference rows stay gray.

Load `show-me` for the comparison itself, including scale and measurement-frame
discipline ([quantitative comparison](../show-me/references/representations.md#quantitative-comparison)).

## The "so what" layer

**Memo mode.** Evidence-ordered docs (demand → constraint → evidence → artifact) prove a claim they never actually *state*. Skimmers leave with numbers and no thesis, and the feedback comes back as *"outline the key product callouts in addition to the numbers."* Pre-empt it.

Directly under the statband, add a `.two-col` of **four** `.panel` children (they auto-flow into a 2×2 — no new CSS). Reading order at the fold becomes: title → tagline → the numbers → what the numbers buy. Each panel gets three parts:

1. **`p.claim`** — large serif, ≤10 words, the line a reader repeats in Slack. "Usually you pick two." / "Feasible today. Not yet a product."
2. **`.rows`** — exactly three mono rows. For deltas use `.was`/`.to` (renders `before → after`, arrow and after-value in orange) so the *change* is the visual event. For non-metrics, use the three rows as an option set (three placements; warn/block/redact) — the choice becomes legible without prose.
3. **`p.note`** — one muted sentence carrying the caveat or the mechanism.

Rules that make this work:

- **One panel must be the honest limit.** Give it `.rose`; the template neutralizes its row accents so it doesn't read as a fourth win. A callout block of four unbroken wins reads as marketing and costs you the other three.
- **Don't repeat the statband's headline number as a claim.** Adjacent blocks saying `26×` twice read as one beat stuttering; demote the repeat into `.note`.
- **Prose paragraphs in these panels defeat the purpose.** If a panel needs a paragraph, it belongs in a section, not the fold.
- **Keep the hedges** the body sections were careful about — differing measurement frames, hardware assumptions, scope limits. A summary layer that flattens caveats is how a doc loses its most careful reader.

## Components inventory

All defined in `references/template.html` — read it for any pattern you're unsure of.

| Selector | Purpose | When to use |
|---|---|---|
| `.eyebrow` | Mono uppercase kicker w/ rule | Above titles & figure labels |
| `h1.title` + `.tagline` | Hero | Once, in `header.doc` |
| `.linkline .group` | Borderless mono row of ticket/PR links | Once, after tagline |
| `.statband` | Four quantitative proof points | Memo/internal-sell mode, directly below the hero |
| `figure.demo` | Video poster card | Optional, between header and §1 |
| `section.block > h2/h3` | Numbered eyebrow + display heading | Every section |
| `.lede` + `.dropcap` | First-paragraph treatment | First paragraph of §1 only |
| `.two-col > .panel` | Side-by-side lists | Goals/non-goals, pros/cons |
| `.panel > .claim` + `.rows` + `.note` | Product callout: memorable line, three scannable rows, one caveat | Under the statband, when the numbers need a "so what" — see [The "so what" layer](#the-so-what-layer) |
| `article.decision` | D-card: Decision / Rationale / Alternatives / Consequence | Every key decision — the load-bearing component. Reviewers skim titles, then dt/dd rows. **Bullets are not a substitute.** |
| `aside.pullquote` | Mental-model or thesis quote | 1 per ~1500 words; should literally state the thesis in ≤25 words |
| `figure.diagram` + inline `<svg>` | Container for a show-me visual explanation | Placement chosen by the document's argument |
| `pre.code` w/ `.k`/`.s`/`.t`/`.fn`/`.hl` spans | Selectable code or a show-me code companion | Source and labelling rules belong to show-me |
| `.callout` (`.rose`) | Notes, warnings | Sparingly — every callout devalues the rest |
| `table.kv` | Tradeoff matrices, limits, disposition tables | Comparing N options; function-by-function fate of a displaced system |
| `.table-wrap` | Horizontal scroll for wide tables | Wrap any table with more than ~5 columns |
| `.g-down` / `.g-flat` / `.g-up` / `.g-na` | Effect glyphs `↓ = ↑ ·` (only `↓` is orange) | Goal columns of a changes-and-impact table; `build-md.js` adds them |
| `figure.diagram > img` | Raster figure with caption | Report figures; budget per [publishing](references/publishing.md#size-budget-first) |
| `header.doc .preamble` | Small provenance prose under the hero | Report mode: the source's text before its first section |
| `ol.numbered` | Roman-numeralled list | Open questions |
| `footer.doc` | Provenance (PR · ticket · HEAD sha · file path) | Once, at end |

**Citing code.** Use `<code>name</code>` for function/component names inline. File paths get one explicit anchor at the point of citation: "(see `apps/cli/src/services/scheduled-tasks/loopSchedule.ts:42`)". Reviewers `rg` from names; they don't click.

## Sharing: thumbnail, cards, publishing

Three outputs can accompany the doc; each has one owning reference.

- **Hero thumbnail** for every shared link: `node references/thumbnail.js <abs-path> [out.png] [ratio] [--hero=<selector>]`. Works on any page with an `<h1>`; contract and crop rules in [share images](references/share-images.md#hero-thumbnail).
- **Slack cards** (1600×900): headline numbers, what ships, negatives kept. Skeletons in `references/cards.html`, rendered by `references/render-cards.js`; what belongs on a card in [share images](references/share-images.md#slack-cards). Cards obey the verbatim-numbers rule and carry their measurement frame in the footer.
- **Publishing** only on request: secret gist + gistpreview, the ~1 MB truncation budget, the image re-encoding recipe, update flow, and verified dead ends (including why the link never unfurls into a preview) in [publishing](references/publishing.md). Flat charts: palette PNG (`magick in.png -resize '1400x>' -colors 128 out.png`) or SVG, never JPEG.

Present each PNG path with the doc link and let the user place them.

## Verification checklist

Before declaring done:

**Facts**
- [ ] Every number, id, and verdict in the doc, stat band, thumbnail, and cards matches its source verbatim; in report mode, source prose is unchanged.
- [ ] Every cited constant / file path / function signature was verified with `rg` against source.
- [ ] PR description and code agree on numerics; if not, code wins and the discrepancy is flagged.
- [ ] Every sentence you wrote passed the **voice** sweep.

**Reader** (RFC and memo; in report mode, flag gaps to the source's author)
- [ ] §1 lede passes the zero-context test (plain-words problem + fix, no internal jargon, no leading non-goal).
- [ ] §2 opens with the primer; every motivating ticket is described in-doc — the reader never needs to open the tracker.

**Structure**
- [ ] Title + tagline + section headings read in order as one narrative spine; a conceptual title carries a literal `.subtitle`.
- [ ] The document follows the mode chosen in step 1; memo mode contains no empty RFC sections or vestigial decision cards.
- [ ] If the proposal displaces an existing system, a function-by-function disposition table states each function's fate.
- [ ] Decision cards that touch product surface passed the smallest-vocabulary audit (composition of existing primitives before any new surface).
- [ ] In RFC mode, each `article.decision` has all four `dt` slots: Decision, Rationale, Alternatives rejected, Consequence.
- [ ] Open questions, when present, are ordered by leverage (highest first).
- [ ] No literal "TODO" or `<!-- TODO -->` markers remain.
- [ ] No template furniture: colophon, reviewer roster, section meta-intros, and §1 cross-ref sentences are absent unless the user asked for them.
- [ ] If callout panels are present: each has a `.claim`, one is `.rose` carrying the honest limit, and no headline number is repeated verbatim from the adjacent statband.
- [ ] After inserting any block, the tagline and the section that previously owned the point were swept for duplication.
- [ ] If the doc is being shared as a link, a hero thumbnail was generated, inspected at high quality, and handed to the user with the URL.
- [ ] If cards were made: each is 1600×900 with no overflow warning from `render-cards.js`, carries its measurement frame, and was inspected at high quality.

**Visual**
- [ ] Embedded explanations passed show-me's acceptance and render checks using the document's components.
- [ ] The sweep matched step 5 (full sweep where required, `--sample` otherwise); no contrast failures on charts, tables, diagrams, code blocks, or accent surfaces.
- [ ] No scroll-point is a single unbroken paragraph block — every segment shows at least one structural break.
- [ ] Print stylesheet renders without overflow (Chrome → Cmd-P → check pagination).
- [ ] `scrollHeight` after Pass 2 is ≤ `scrollHeight` after Pass 1. If it grew and no Pass-3 diagram was added, you bloated.
- [ ] Factory mode uses no italics, gradients, shadows, glass, or decorative second accent.
- [ ] Orange identifies the primary path or proof point; controls and reference rows remain neutral.

**Publish**
- [ ] The file is under ~1 MB (flat charts palette-encoded or SVG).
- [ ] After any gist create/PATCH, the [publishing](references/publishing.md) truncation and footer checks passed.

## Dead ends (warnings)

- ⚠️ **Don't inspect only the dark hero.** The full dark scroll catches failures in lower charts, tables, diagrams, and callouts that the first viewport cannot.
- ⚠️ **Don't use orange as ambient decoration.** If every border, heading, and comparison row is orange, nothing is primary. Keep controls and secondary comparisons gray.
- ⚠️ **Don't bring gradients or shadows back to create “depth.”** Factory surfaces use contrast, borders, spacing, and type.
- ⚠️ **Don't put the same enumeration in §3 Goals AND §5 Decisions.** Pick the canonical home (usually a decision card) and forward-reference from elsewhere.
- ⚠️ **Don't remove `.decision dd { grid-column: 2 }`.** Without it, `dd` falls under `dt` instead of into column 2. Most browsers won't warn.
- ⚠️ **Don't revert the auto-hide TOC** (`nav.toc` → 68px rail expanding to 248px on hover) **to a sticky 220px sidebar.** Content reads worse with the sidebar always present. Don't shrink the rail below 68px either — 56px clips "VIII" to "VII".
- ⚠️ **Don't let decision cards mint product surface unexamined.** New verbs, flags, config axes, parallel stores, and named presets reliably draw "this is ugly" review — one session took three consecutive rounds, each one level deeper (CLI flags → a dual dossier store → presets layered over existing settings). Audit each card for the smallest vocabulary that still composes into the full feature set: prefer composition of existing primitives over any new surface, and one orthogonal primitive over a parallel mechanism. When the design genuinely adds no surface, say so — "the primitive already ships" is the strongest selling line.
- ⚠️ **Don't answer "make it punchier" by trimming sentences.** Shorter paragraphs are still paragraphs, and still get skipped. Change the *structure* — claim line, scannable rows, one caveat ([The "so what" layer](#the-so-what-layer)). Restructuring cut one doc's body copy ~60% and its panel height from 393px to ~280px; word-level trimming would not have.
- ⚠️ **Don't make a secret-gist URL public-shareable** without confirming with the user. The doc may reference internal Linear tickets, employees, or unmerged architecture.

## References

- [show-me rendering and embedding](../show-me/references/surfaces.md) — shared visual-explanation owner; load through `show-me`, not as a second document workflow.
- `references/template.html` — full Factory-themed HTML scaffold to copy, with RFC components and an optional memo proof band; also the one stylesheet `build-md.js` renders with.
- `references/report-mode.md` — report/retrospective spine, changes-table glyphs, builder usage, and the AC-949 worked example.
- `references/build-md.js` — markdown → design-doc HTML. `node build-md.js <source.md> <out.html> [--eyebrow=..] [--hero=f.html] [--footer=f.html] [--linked-images]`.
- `references/share-images.md` — hero thumbnail contract and Slack card guidance.
- `references/cards.html` + `references/render-cards.js` — three card archetypes; `node render-cards.js <cards.html> [out-dir]`.
- `references/publishing.md` — gist flow, size budget and image encoding, dead ends.
- `references/screenshot.js` — Playwright capture. `node screenshot.js <abs-path-to-html> [out-dir] [--sample]`.
- `references/inspect.js` — DOM probe for layout debugging. `node inspect.js <abs-path> "<selector>"`.
- `references/thumbnail.js` — hero crop for sharing a doc link. `node thumbnail.js <abs-path> [out.png] [ratio] [--hero=<selector>]`.
- `references/lib.js` — shared module resolution and arg parsing for the scripts.
