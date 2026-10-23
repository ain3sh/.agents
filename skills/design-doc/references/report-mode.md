# Report mode: retrospectives, measurement reports, changes-and-impact memos

Use when the argument already exists as markdown (a retro, findings file,
ledger summary) and the job is to render it, not to argue a proposal. The
source's structure is the structure; there are no decision cards or goals.

## Fidelity is the rule

Prose, numbers, ids, verdicts, and claims pass through **verbatim**. Only
layout changes. Anything written fresh (eyebrow, lede, metrics, headline,
findings, cards) carries only values copied from the source, with their block
or id. If the source is wrong, flag it to the author; never fix it in the
render.

## Two builds

**Plain**: every source section becomes a page section, in order.

```bash
node ~/.agents/skills/design-doc/references/build-md.js <source.md> <out.html> \
  --eyebrow="TICKET · Retrospective · YYYY-MM-DD" --hero=hero.html
```

**Curated front** (preferred for anything shared beyond the authors): you write
the headline, findings, and story as a fragment; the whole source then renders
verbatim inside a collapsed "Full report" log, so nothing is dropped and nothing
is in the skimmer's way.

```bash
node ~/.agents/skills/design-doc/references/build-md.js <source.md> <out.html> \
  --eyebrow="..." --hero=hero.html --front=front.html
```

`front.html` is a sequence of `<section id="..." data-nav="Label">` blocks
using template components: a `.headline`, a `.findings` grid whose cards link
to `#<slug-of-source-heading>` anchors inside the log (the builder ids every
source section and `###` heading), and optionally a `.timeline` of the arc.
Each `data-nav` becomes a top-bar link; "Full report" is appended. A link
into the log opens it and scrolls to the target (the template script handles
any `#hash` inside a `<details>`).

`hero.html` holds what follows the title: `.lede`, `.linkline`, `.metrics`. It
is raw HTML, so write `<code>` rather than markdown backticks.

`--title="<claim>"` makes the h1 a claim without editing the source: the
source `# Title` becomes the h1's `.subtitle` and stays the `<title>` (search,
Slack unfurls). Use it whenever the source title is a filing label
("…: retrospective").

## What the builder maps

- `# Title` → hero `h1` and `<title>` (with `--title`, the h1's `.subtitle`);
  text before the first `##` → the hero `.preamble` (with `--front`, atop the
  full report).
- `## 3. Heading` → section with `.slabel` `03 / Heading` and an `h2` (with
  `--front`: a log chapter numbered `03`). Unnumbered `##` → `h2` alone and
  an unnumbered chapter: numbers are the source's own, never positions, so
  prose citing "§7" matches the page. Nav labels are the heading up to its
  first `:`, `,`, `; `, `(`, or `—`.
- With `--front`, a `nav.toc` right under the "Full report" summary lists
  every chapter by its source `§` and links to it.
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
[verify](verify.md). The full sweep opens the log, so the verbatim source is
checked too.

## Worked example

The AC-949 PTC retrospective (`ac-949` worktree):

- source: `.agents/ledgers/RETRO-ac-949-ptc.md`
- old render: `.agents/ledgers/live/results/retro-site/AC-949-PTC-retro.html`
  (a 45,905px raw-markdown dump on the previous light/dark template: the
  failure `--front` exists to fix)
- cards: `.agents/ledgers/live/results/retro-site/cards.html` and `card-*.png`
