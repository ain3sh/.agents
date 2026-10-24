# Report mode: retrospectives, measurement reports, changes-and-impact memos

Use when the argument already exists as markdown (a retro, findings file,
ledger summary) and the job is to render it, not to argue a proposal. The
source's structure is the structure; there are no decision cards or goals.

## Fidelity is the rule

Every number, date, id, verdict, and quote matches the source character for
character. Prose may be rewritten and laid out with components (the curated
front always; report chapters through `--log-dir`), but a rewrite carries only
values copied from the source, with their block or id, and drops nothing the
source claims. If the source is wrong, flag it to the author; never fix it in
the render. Without a rewrite, a section renders verbatim.

## Two builds

**Plain**: every source section becomes a page section, in order.

```bash
node ~/.agents/skills/design-doc/references/build-md.js <source.md> <out.html> \
  --eyebrow="TICKET · Retrospective · YYYY-MM-DD" --hero=hero.html
```

**Curated front** (preferred for anything shared beyond the authors): you write
the headline, findings, and story as a fragment; the whole source then renders
as the "Full report" section, one collapsed chapter per source section, so
nothing is dropped and nothing is in the skimmer's way.

```bash
node ~/.agents/skills/design-doc/references/build-md.js <source.md> <out.html> \
  --eyebrow="..." --hero=hero.html --front=front.html \
  --log-dir=frags/log --source-url=https://gist.github.com/<id>
```

`front.html` is a sequence of `<section id="..." data-nav="Label">` blocks
using template components: a `.headline`, a `.findings` grid whose cards link
to `#<slug-of-source-heading>` anchors inside the log (the builder ids every
source section and `###` heading), and optionally a `.timeline` of the arc.
Each `data-nav` becomes a top-bar link; "Full report" is appended. A link
into the report opens the chapter around its target and scrolls to it (the
template script opens every `<details>` around any `#hash`, on load, on
hashchange, and on click).

The full report, top to bottom:

1. `.slabel` "Source", `h2` "The full report", and `.report-bar`: one line
   counting the sections and how they render ("The source report, verbatim:
   14 sections"; with every section rewritten, "Every section of the source
   report, rewritten and checked against it: 14 sections"; mixed builds name
   both) and an Expand all / Collapse all `.report-toggle`.
2. `.tiles`, the chapter index: one `a.tile` per section in source order.
   `.tile-n` is the marker: `.tile-s` holds the source `§N` (empty for an
   unnumbered section, drawn as a neutral dot when nothing follows it) and
   `.tile-h` the source heading when the chapter has a claim title. `.tile-t`
   is the title; `.tile-m` a meta line counted at build time, such as "6 min ·
   4 tables · 2 figures", where figures include `<!-- viz-NN -->` and
   `<!-- chart-log:… -->` placeholders filled after the build. One grid, no
   group labels, once every section is rewritten. While unnumbered sections
   still render verbatim, they group first under "Front matter, curated
   above", then numbered ones under "Chapters". Three columns, two below
   1100px; on phones, one-line rows of number and title (an unnumbered row
   keeps its source heading above the title; meta is dropped). Hidden in print.
3. `.report-about`: the source's text before its first `##` (provenance),
   verbatim, as a small note under the index, ending in a "Source of record"
   link when `--source-url` is given.
4. `.chapters` of `details.chap`, each collapsed, its `summary` a section
   header (`.chn` marker line, `.cht` title, `.chm` meta, chevron) and its
   `.chb` body at the page's widths: prose at the reading measure, tables and
   figures across the full column. Print opens every chapter.

### Rewritten chapters (`--log-dir`)

`--log-dir=<dir>` reads `<dir>/<section-id>.html` for each source section;
the id is the slug the builder gives the `##` heading (`3-the-arc-block-by-block`,
`tl-dr`). When the file exists it replaces that section's body outright: the
markdown is not rendered beside it, so ids stay unique. A first line of
`<!-- title: <claim> -->` becomes the chapter's `.cht` and tile title, and the
source heading moves to the marker line (`§3 · The arc, block by block`). The
build prints `log-dir: N/M sections rewritten` and names the sections still
rendered from markdown.

A chapter body is raw HTML using template components. Inside `.chb`, a
`.timeline` runs a tighter rhythm than on the page so a long arc stays
scannable. For a source's own caveat, use `<p class="note src">`: the template
labels it "Source note", so do not repeat that text. A `<span class="dim mono">`
after a table key cell's text drops to a small secondary line (an id or block
under a name). Anchors the front links to (`#<slug>`) must exist in the
rewrite; the verify sweep checks every `#` link resolves.

`hero.html` holds what follows the title: `.lede`, `.linkline`, `.metrics`. It
is raw HTML, so write `<code>` rather than markdown backticks.

`--title="<claim>"` makes the h1 a claim without editing the source: the
source `# Title` becomes the h1's `.subtitle` and stays the `<title>` (search,
Slack unfurls). Use it whenever the source title is a filing label
("…: retrospective").

## What the builder maps

- `# Title` → hero `h1` and `<title>` (with `--title`, the h1's `.subtitle`);
  text before the first `##` → the hero `.preamble` (with `--front`, the
  report's `.report-about` note).
- `## 3. Heading` → section with `.slabel` `03 / Heading` and an `h2` (with
  `--front`: a chapter marked `§3`). Unnumbered `##` → `h2` alone and
  an unnumbered chapter: numbers are the source's own, never positions, so
  prose citing "§7" matches the page. Nav labels are the heading up to its
  first `:`, `,`, `; `, `(`, or `—`.
- `###` / `####` → `h3` / `h4` with slug ids.
- `![alt](img)` followed by an `*italic caption*` line → `figure.diagram`.
  Images embed as base64 unless `--linked-images`.
- Tables → `.table-wrap table`; `|---:|` columns get `.num`; a cell starting
  with `↓ ↑ = ·` gets its effect-glyph span; 4+ columns or any cell over 60
  characters adds `table.stack` (cards on phones).
- Lists → `ul.bullets` / `ol.steps`; blockquotes → `.callout`; fenced code →
  `pre.code`.
- `--footer=f.html` replaces the default provenance line (source file name and
  render date).

Styles, logo, and script are read from `template.html` at build time; there is
no second stylesheet to drift. The builder warns past ~1 MB (gist drafts
truncate; conjure does not).

## Spine of a good report

Keep the source's order when it differs; flag gaps to its author.

1. **TL;DR**: the end state per goal with its final number and the block that
   measured it; the starting point; how (causes removed, not effort spent).
2. **Figures**: captions state the finding and its frame (n, block,
   same-day/same-binary).
3. **Changes and their impact**: one row per change tried, never grouped.
   Columns: change, what it does, one column per goal, outcome, evidence block.
   Goal cells lead with `↓` improved, `=` no measurable effect, `↑` regressed,
   `·` not the target; state that legend in prose above the table.
4. **Numbered sections**: the question asked; where it ended (a scoreboard, one
   row per preregistered clause with its verdict); the arc block by block; what
   was learned; negative results kept; residuals and open questions; shipping
   state; process.

With `--front`, items 1–3 are what the front distils: the TL;DR becomes the
headline and metrics, the strongest measured changes become findings (the
closest call or a negative result is the `.limit` card), and the arc becomes a
timeline.

## Verify

`screenshot.js --sample` (one stylesheet, so one instance per component is
representative), plus a full sweep and `--print` before sharing; see
[verify](verify.md). The full sweep opens the log, so every chapter is checked
too.

## Worked example

The AC-949 PTC retrospective (`ac-949` worktree):

- source: `.agents/ledgers/RETRO-ac-949-ptc.md`
- old render: `.agents/ledgers/live/results/retro-site/AC-949-PTC-retro.html`
  (a 45,905px raw-markdown dump on the previous light/dark template: the
  failure `--front` exists to fix)
- cards: `.agents/ledgers/live/results/retro-site/cards.html` and `card-*.png`
