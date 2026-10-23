# Share images: hero thumbnail and Slack cards

A doc link in chat renders as a bare URL (neither gistpreview nor SSO-gated
conjure unfurls) and gets scrolled past. Two image outputs travel with it, both
on the template's dark tokens, both carrying only numbers copied verbatim from
the page.

| Output | Size | When |
|---|---|---|
| Hero thumbnail | 1.6:1 crop at 2x | Every shared link: eyebrow, title, lede, metrics |
| Slack cards | 1600×900 at 1x | When the argument has more than one postable beat: results, what ships, what failed |

Read either at `image_quality="high"` before handing it over; bleed, centring,
and clipping bugs are invisible at default quality. Hand over each PNG path
with the doc link and let the user place them.

## Hero thumbnail

```bash
node ~/.agents/skills/design-doc/references/thumbnail.js <abs.html> [out.png] [ratio] [--hero=<selector>]
```

Works on any page: the hero is `--hero`, else the first `<header>` holding an
`<h1>`, else the first `<h1>`'s parent. The crop ends at `.metrics`,
`.linkline`, or `.lede`, whichever the hero has first. It renders at a 1440px
viewport with reduced motion (the typed lede is complete), makes every `<nav>`
and every fixed or sticky element invisible (layout kept, so a grid sidebar
does not reflow the hero), hides everything after the anchor so nothing bleeds
into the bottom edge, and centres on the wider of hero and anchor.

## Slack cards

Cards are postable snippets of the doc, one beat each. They were the most
reused artifact of the AC-949 retrospective; treat them as a first-class
output.

**What goes on a card**

- **One claim as the heading**, ≤8 words, that a reader could repeat.
- **Numbers copied from the doc**, never recomputed or re-rounded, each with
  its block, build, or id in the footer or a caption line.
- **The measurement frame and quality gate in the footer** ("142 of 144 cells
  at 1.0 · same day, same binary"). A card without its frame is how a number
  escapes its caveats.
- **The honest limit stays visible**: the close-call row on a results card, the
  not-selected option on a ships card.

**Three archetypes** (skeletons in `cards.html`):

1. **Headline numbers** (`card-headline`): one column per goal: the goal as a
   reader says it, one big white number, its denominator, a meter (`.col.pri`
   gets the accent gradient, others grey), and three breakdown rows including
   the closest call.
2. **What ships** (`card-ships`): one row per change: id, what it does, its
   measured effect, destination PR, plus a dashed note for the measured option
   that was not selected.
3. **Negatives kept** (`card-negatives`): a 3×2 grid of arms that failed:
   name, the number that killed it, why in one sentence, block ids. Values stay
   neutral; orange is for wins.

**Render**

```bash
cp ~/.agents/skills/design-doc/references/cards.html <doc-dir>/cards.html   # fill the [bracketed] values
node ~/.agents/skills/design-doc/references/render-cards.js <doc-dir>/cards.html [out-dir]
```

Each `<section class="card" id="card-...">` becomes `card-....png` at exactly
1600×900. The script warns when content overflows the card; fix by cutting
rows, never by shrinking type below the template sizes. Keep decoration inside
the card box: anything positioned past the edge also trips the warning.

Worked example: the AC-949 retrospective cards, `ac-949` worktree,
`.agents/ledgers/live/results/retro-site/cards.html` and its three PNGs
(made on the previous light/dark tokens).
