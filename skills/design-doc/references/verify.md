# Verify: the sweep loop and the pre-share checklist

## Loop

Write → capture → read → fix, then content passes, then capture again.

```bash
R=~/.agents/skills/design-doc/references
node $R/screenshot.js <abs.html> [out-dir]            # full sweep → scroll-NN.png (default /tmp/doc-previews)
node $R/screenshot.js <abs.html> [out-dir] --sample   # hero + first instance of each component → sample-NN-<component>.png
node $R/screenshot.js <abs.html> [out-dir] --print    # also doc.pdf (A4, print media)
```

Captures run at 1360px, 2x, with reduced motion (reveals and typed text
settled) and every `<details>` opened, so the collapsed log is checked too. The
scripts work on any HTML page and force `scroll-behavior: auto`, without which
every segment would capture the top of the page.

Modules resolve through `lib.js`: `$PLAYWRIGHT_NODE_MODULES`, `$NODE_PATH`,
every `node_modules` above the CWD, then `npm root -g`. One global install
covers every project: `npm i -g playwright marked && playwright install chromium`.

## Which sweep

- **Full sweep, every segment**: first render of a hand-authored page, after
  any CSS or template edit, after adding a component type or a show-me view, and
  once before sharing. Read hero, table, chart, diagram, and code segments at
  `image_quality="high"`; prose segments at default, re-read high if something
  looks off.
- **`--sample` is enough** while iterating on content in a page whose layout
  already passed a full sweep, and for `build-md.js` output, where one
  stylesheet renders every instance of a component the same way. Read every
  sample at high quality.
- **Motion check** once before sharing: the sweep runs with reduced motion, so
  capture Fig 1 and every `data-motion` figure after a few seconds with motion
  on (animate-process `capture.mjs` on the doc, or a Playwright shot without
  `reducedMotion`) and read them.
- **`--print` once before sharing**: check the PDF for clipped tables, split
  cards, and that the log printed open.

Fix layout, contrast, and overflow before tightening prose. Bugs only a capture
shows:

- `dd` falling under `dt` in a decision card: restore
  `.decision dd { grid-column: 2 }` if a copied card lost it.
- A wide table or SVG overflowing its card at 1360px.
- Low contrast on `--meta` text over `--surface`, or a value on an accent fill.
- Embedded views failing [show-me's render checks](../../show-me/references/surfaces.md#browser)
  at the page's real content width (1080px inside `.wrap`).
- A nav link whose `href` matches no `id`, so the scroll-spy never lights it.
- Dark page margins in `doc.pdf`: the print block must keep
  `:root { color-scheme: light }` (`:root`, not `html`, or the screen rule's
  specificity wins).

When layout is mysterious, `node $R/inspect.js <abs.html> "<selector>"` dumps
the rect and computed styles (display, grid-column, position, colour, font,
opacity) of the first 12 matches.

## Re-verify

Re-run the sweep after the content passes. **`scrollHeight` should drop, not
grow**: one doc went 18820 → 18429px and 17 → 14 segments with no information
lost. The only sanctioned growth is a figure; prose height still shrinks, and
`prose.js` must pass.

## Checklist before sharing

**Facts**
- [ ] Every number, id, and verdict in the page, metrics, thumbnail, and cards matches its source verbatim; in report mode the source prose is unchanged.
- [ ] Every cited constant, path, and signature was verified with `rg`; PR/code disagreements are flagged.
- [ ] Every sentence you wrote passed the **voice** sweep.

**Reader** (RFC and memo; in report mode, flag gaps to the source's author)
- [ ] The lede passes the zero-context test: plain problem + fix, no internal jargon, no leading non-goal.
- [ ] Context opens with the primer; every motivating ticket is described in the page.

**Structure**
- [ ] Title, lede, and nav labels read in order as one spine; a conceptual title carries a literal `.subtitle`.
- [ ] The page follows the chosen mode; no empty RFC sections or vestigial decision cards in a memo.
- [ ] The headline states the answer, the evidence, and the caveat; findings each link to their evidence and one is `.limit`; no metric value repeats as a finding claim.
- [ ] A displaced system has its disposition table.
- [ ] An RFC compares every credible rival in Alternatives; the history grep in [structure](structure.md#the-final-design-not-the-prs-history) leaves no narration of the PR.
- [ ] Decisions are one table that passed the smallest-vocabulary audit; at most two promoted cards, each with all four `dt` slots.
- [ ] Fig 1 shows the mechanism moving under the headline, read from a motion capture.
- [ ] Open questions are ordered by leverage.
- [ ] No TODO markers; no colophon, roster, meta-intros, or navigational sentences.
- [ ] After any insertion, the lede and the section that owned the point were swept for duplication.
- [ ] A shared link has a thumbnail, read at high quality; cards are 1600×900 with no overflow warning, carry their frame, and were read at high quality.

**Visual**
- [ ] The sweep matched "Which sweep"; embedded views passed show-me's checks.
- [ ] No viewport is a single unbroken paragraph block.
- [ ] `doc.pdf` paginates without clipped tables or split cards.
- [ ] `scrollHeight` after the content passes ≤ before, unless a figure was added; `prose.js` passes.
- [ ] Orange marks only the primary path, labels, and live state; controls stay grey; no italics, shadows, or extra decoration.

**Publish**
- [ ] A gist draft is under ~1 MB and passed the truncation check; a conjure deploy was asked for and its URL loads (see [publishing](publishing.md)).
