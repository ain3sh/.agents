# Share images: hero thumbnail and Slack cards

A doc link in chat renders as a bare URL and gets scrolled past. Two image
outputs travel with it. Both are dark mode, both carry only numbers copied
verbatim from the doc.

| Output | Size | When |
|---|---|---|
| Hero thumbnail | 1.6:1 crop at 2x | Every shared link: title, tagline, stat band |
| Slack cards | 1600×900 at 1x | When the argument has more than one beat worth posting: results, what ships, what failed |

Verify either with a `Read` at `image_quality="high"` before handing it over;
bleed, centring, and clipping bugs are invisible at default quality.

## Hero thumbnail

```bash
node ~/.agents/skills/design-doc/references/thumbnail.js <abs-path-to-html> [out.png] [ratio] [--hero=<selector>]
```

Works on any page: the hero is `--hero`, else `header.doc`, else the first
`<header>` holding an `<h1>`, else the first `<h1>`'s parent. The crop ends at
`.statband`, `.meta`, `.linkline`, or `.tagline`, whichever the hero has first.
It makes every `<nav>` invisible (keeping layout, so a grid sidebar does not
reflow the hero), hides everything after the anchor so no accent sliver bleeds
into the bottom edge, and centres on the wider of hero and anchor, because the
stat band is usually wider than the header.

## Slack cards

Cards are postable snippets of the doc, one beat each. They were the most
reused artifact of the AC-949 retrospective; treat them as a first-class
output, not an afterthought.

**What goes on a card**

- **One claim as the heading**, ≤ 8 words, that a reader could repeat.
- **Numbers copied from the doc**, never recomputed or rounded differently,
  each with its block, build, or id in the footer or a caption line.
- **The measurement frame and quality gate in the footer** (for example
  "142 of 144 cells at 1.0 · same day, same binary"). A card without its frame
  is how a number escapes its caveats.
- **The honest limit stays visible**: the close call row on a results card,
  the not-selected option on a ships card.

**Three archetypes** (skeletons in `cards.html`):

1. **Headline numbers** (`card-headline`): one column per goal: goal as the
   reader says it, one big accent number, its denominator, three breakdown
   rows including the closest call.
2. **What ships** (`card-ships`): one row per change: id, what it does, its
   measured effect, destination PR, plus a dashed note for the measured option
   that was not selected.
3. **Negatives kept** (`card-negatives`): a 3×2 grid of arms that failed:
   name, the number that killed it, why in one sentence, block ids. Values stay
   neutral ink; orange is for wins.

**Render**

```bash
cp ~/.agents/skills/design-doc/references/cards.html <doc-dir>/cards.html   # fill the [bracketed] values
node ~/.agents/skills/design-doc/references/render-cards.js <doc-dir>/cards.html [out-dir]
```

Each `<section class="card" id="card-...">` becomes `card-....png` at exactly
1600×900. The script warns when content overflows the card and is clipped;
fix by cutting rows, not by shrinking type below the template sizes.

Worked example: the AC-949 retrospective cards, in the `ac-949` worktree at
`.agents/ledgers/live/results/retro-site/cards.html` with its three PNGs.
