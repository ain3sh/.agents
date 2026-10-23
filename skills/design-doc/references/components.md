# Components: visual system, progressive disclosure, inventory

Every selector below is defined in `template.html`; read it for any pattern
you are unsure of. Tokens come from the Factory brand guide's Tungsten ramp, so
use the existing custom properties and never invent intermediate greys.

## Visual system

- **Dark only.** Black canvas, white headlines and values, warm Tungsten greys
  for body (`--body`), metadata (`--meta`), and surfaces (`--surface`,
  `--surface2`). Print switches to paper colours automatically.
- **One accent, `#FF5A00`**, for the live dot, section labels, the primary bar
  or table row, finding numbers, and the active nav dot. The accent gradient
  (`--grad`) fills only the primary data bar or meter; comparison bars are
  hollow or grey.
- **Flat surfaces.** Depth comes from surface contrast, 1px borders, spacing,
  and type. No shadows, glass, or glows; the only blur is the sticky top bar's
  backdrop.
- **Brand texture, once.** The hero's faint grid and halftone rotor, and the
  footer's small spinning rotor, are the decoration budget. Do not add more.
- **Mono-led metadata.** Geist Mono for labels, eyebrows, axes, code, and the
  lede; Geist for headings and prose. No italics (`em` renders upright).
- **Geometry.** 4px radius everywhere; pills only for real status tags.

If the repo defines a different canon, adapt the tokens to it rather than
inventing a theme because the artifact is standalone.

## Type scale

| Role | Treatment |
|---|---|
| `body` | Geist 400, 16.5px / 1.62, tracking −0.01em |
| `h1` | Geist 400, 72px / 1.0, tracking −0.035em, white; `.subtitle` at 0.34em in `--soft2` |
| `.lede` | Geist Mono 400, 15px / 1.6, `--soft2`, ≤680px |
| `.slabel` | Geist Mono 12px uppercase, accent: `01 / Context` |
| `h2` | Geist 400, 40px, tracking −0.03em |
| `h3` | Geist 400, 21px; inside a finding 22px |
| `.mval` | Geist 400, 52px, white, tabular numbers |
| Mono labels | 10.5–12px uppercase, tracking 0.05em; `font-feature-settings: "zero"` on code |

Hierarchy comes from scale, never from orange or bold weight. Headings,
captions, and decision titles use `text-wrap: balance`; paragraphs use
`pretty`.

## Progressive disclosure

The reference look exists to answer one complaint: evidence-ordered docs prove
a claim they never state, so skimmers leave with numbers and no thesis ("outline
the key product callouts in addition to the numbers"). Order the page so each
layer is optional for the reader who already has enough:

1. **Hero metrics** (`.metrics`): four numbers that carry the thesis. Values
   white; `.meter .fill` with `--w` shows a share of a whole.
2. **Headline** (`.headline`): the answer as one bold sentence, the evidence,
   and the caveat in `.hnote`.
3. **Findings** (`.findings > a.finding`): 2–4 claim cards (`.findings.three`
   for three across), each linking to the table, chart, or section that proves
   it. Per card:
   - `h3`: the line a reader repeats in Slack, ≤10 words ("Usually you pick
     two." / "Feasible today. Not yet a product.").
   - `p`: one sentence with the verbatim number and its frame.
   - optional `.rows`: up to three `.r` rows of `.k` label and `.v` value; for
     deltas use `<span class="was">` and `<span class="to">`, which renders
     `before → after` so the change is the visual event. For non-metrics, the
     rows can be an option set (warn / block / redact).
   - `.flink`: the evidence name and arrow.
4. **The story**: the sections, dated where time matters (`.timeline`,
   `.entries`).
5. **The full log** (`details.log` with `.chap` chapters): everything else,
   collapsed. `build-md.js --front` puts a whole source report here verbatim.

Rules for the findings layer:

- **One card is the honest limit** (`.finding.limit`): its number and arrow go
  neutral so it never reads as another win.
- **Don't repeat a metric's value as a finding claim.** Two adjacent blocks
  saying `26×` read as one beat stuttering; demote the repeat into the card's
  sentence.
- **No paragraphs in cards.** A card that needs one belongs in a section.
- **Keep the hedges** the body is careful about: measurement frames, hardware,
  scope. A summary layer that flattens caveats loses the careful reader.

## Quantitative proof

- **Tables**: wrap in `.table-wrap`; right-align numeric columns with `.num`;
  mark the shipped or recommended row `tr.pri` (accent edge, raised surface);
  counts as `<span class="den">(n/N)</span>`; verdicts as `.pill.ok|miss|run|idle`.
- **Bar chart** (`figure.chart` with inline SVG): grey bars, the primary bar
  filled with a per-chart `linearGradient` (unique `id` per chart), white value
  label only on the primary. The template comment gives the y-scale formula.
- **Comparison bars** (`.bars`, `--cols` measures): controls hollow, `.bar-row.pri`
  filled. Use when several arms are compared on 1–3 measures.
- Load **show-me** for the comparison design itself, including scale and
  measurement-frame discipline
  ([quantitative comparison](../../show-me/references/representations.md#quantitative-comparison)).
  Never paste a foreign raster chart when the data can be drawn in-theme.

## Motion

Progressive enhancement only: `.rv` elements fade up when scrolled into view,
meters and bars grow, the `.lede[data-typed]` types in, the live dot flickers.
`prefers-reduced-motion` disables all of it and the bundled scripts capture with
reduced motion, so captures always show settled content. With JS off, `body.nojs`
keeps everything visible. A new revealed block needs only the `rv` class.

## Inventory

| Selector | Purpose | When |
|---|---|---|
| `header.top` + `nav a` | Sticky bar: logo, one link per section, scroll-spy dot | Always; ~8 links max |
| `header.hero` | Grid + halftone rotor backdrop | Once |
| `.eyebrow` (`.live`, `.sep`) | Mono kicker: `kind // area // date` | Hero, and `.lhead` in blocks |
| `h1` (+ `.subtitle`) | Title (+ literal subject) | Once |
| `.lede[data-typed]` | The claim in ≤25 plain words | Once, under the title |
| `.linkline` | Mono row of ticket/PR links | Once, optional |
| `.chat .chat-b[data-prompt]` | Copies a "read this page in Droid" prompt | Conjure-hosted pages only |
| `.metrics > .metric` | Four proof numbers | Hero, when four numbers carry the thesis |
| `.headline` (`.lhead`, `.hnote`) | Bottom line; also the proposal's mental model | First block of `main`; once in Proposal |
| `.entries` (`li.now`) | Key column + title + body rows | Updates, motivating tickets, open items |
| `.findings > a.finding` (`.limit`) | Claim cards linked to evidence | Evidence, memo fronts |
| `.two-col > .panel` (`.limit`) | Side-by-side lists | Goals / non-goals, pros / cons |
| `.timeline > li` (`.now`) | Dated arc | Rollout, retros |
| `.stages > .stage` (`.on`) + `.pill` | Phases with status | Rollout |
| `.table-wrap table` (`tr.pri`, `.num`, `.den`) | Tables, disposition tables | Any comparison of N options |
| `.g-down` `.g-flat` `.g-up` `.g-na` | Effect glyphs `↓ = ↑ ·` (only `↓` is orange) | Changes-and-impact tables; `build-md.js` adds them |
| `figure.chart` | In-theme SVG bar chart | Quantitative comparison |
| `.bars` (`.bar-row.pri`) | Horizontal comparison rows | Arms × measures |
| `figure.diagram` (`svg` or `img`) | Container for a show-me view or a raster figure | Where the question arises |
| `.iso > .iso-figure` | Interactive isometric machine figure, built by **animate-process** and pasted as a fragment | A mechanism the reader should play with; never inside `figure.diagram` |
| `figure.demo` | Video poster card | Optional, after the headline |
| `article.decision` | D-card: Decision / Rationale / Alternatives rejected / Consequence | Every key decision; bullets are no substitute |
| `pre.code` (`.k` `.s` `.t` `.fn` `.comment` `.hl`) + `.code-caption` | Code with one highlighted line | Source and labelling rules belong to show-me |
| `.callout` (`.limit`) | Note or warning | Sparingly; each one devalues the rest |
| `ol.numbered` (`.q`, `.a`) | Numbered questions | Open questions, by leverage |
| `ol.steps`, `ul.bullets` | Plain lists | Body prose |
| `details.log` + `.chap` | Collapsed full record | End of `main` |
| `header.hero .preamble` | Small provenance prose under the hero | Report mode: source text before its first section |
| `footer.doc` (`.frotor`) | Provenance | Once |
