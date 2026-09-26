# Report mode: retrospectives, measurement reports, changes-and-impact memos

Use when the argument already exists as a markdown source (a retro, findings
file, ledger summary) and the job is to render it, not to argue a proposal.
The RFC scaffold does not fit: there are no decision cards or goals/non-goals,
and the source's structure is the structure.

## Fidelity is the rule

Prose, numbers, ids, verdicts, and claims pass through **verbatim**. Only
layout changes: sections, figures, tables, glyph spans. Anything written fresh
(eyebrow, tagline, stat band, cards) carries only values copied from the
source, with their block or id. If the source is wrong, flag it to the author;
do not fix it in the render.

## Spine

A report reads well in this order; keep the source's order when it differs.

1. **TL;DR**: the end state per goal with its final number and the block that
   measured it; the starting point; how (causes removed, not effort spent).
2. **Figures**: each with a caption that states the finding and its frame
   (n, block, same-day/same-binary).
3. **Changes and their impact**: one row per change tried, never grouped.
   Columns: change, what it does, one column per goal, outcome, evidence
   block. Goal cells lead with a glyph: `↓` improved, `=` no measurable effect,
   `↑` regressed, `·` not the target; state that legend in prose above the
   table.
4. **Numbered sections**: the question asked; where it ended (a scoreboard
   table, one row per preregistered clause with its verdict); the arc block by
   block; what was learned; negative results kept; residuals and open
   questions; shipping state; process.

## Build from markdown

```bash
node ~/.agents/skills/design-doc/references/build-md.js <source.md> <out.html> \
  --eyebrow="TICKET · Retrospective · YYYY-MM-DD" --hero=hero.html
```

- The stylesheet is `template.html`'s, read at build time; there is no second
  CSS to drift.
- `# Title` becomes the hero title; text before the first `##` becomes a small
  provenance block under the hero.
- `## 3. Heading` becomes `§3` plus a display heading; unnumbered `##` gets
  the display heading alone. `###` and `####` become `h4` and `h5`.
- `![alt](img)` followed by an `*italic caption*` line becomes a
  `figure.diagram`. Images embed as base64 unless `--linked-images`.
- Tables become `table.kv` in a scrolling `.table-wrap`; a cell starting with
  `↓ ↑ = ·` gets the effect-glyph span.
- `--hero` is an HTML fragment placed after the title: `.tagline`, `.linkline`,
  `.statband`, and the `.two-col` callout panels from the template.

The collapsed TOC rail fits roman numerals up to four characters (through
XVII); the builder warns past 17 sections.

Verify with `screenshot.js --sample` (one stylesheet, so one instance per
component is representative) plus a full sweep before sharing; see the
iteration loop in SKILL.md.

## Worked example

The AC-949 PTC retrospective, in the `ac-949` worktree:

- source: `.agents/ledgers/RETRO-ac-949-ptc.md`
- render: `.agents/ledgers/live/results/retro-site/AC-949-PTC-retro.html`
- cards: `.agents/ledgers/live/results/retro-site/cards.html` and `card-*.png`

That render predates `build-md.js` and uses its own `build.mjs`/`retro.css`
with an always-visible sticky sidebar; `build-md.js` is the generalized
version on the canonical stylesheet and rail. Rebuilding the same source with
`build-md.js` produces an equivalent document.
