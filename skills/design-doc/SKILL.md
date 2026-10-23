---
name: design-doc
description: "Author a single-file HTML design doc, memo, or rendered report in Factory's dark visual system, plus Slack cards and a hero thumbnail; Playwright-verified, published as a secret-gist draft or a conjure site."
disable-model-invocation: true
---

A design doc here is one self-contained, dark HTML page (Geist via Google Fonts, inline styles, a few lines of vanilla JS) that reads like the Factory product: the bottom line first, claims linked to their evidence, and the full record one click away instead of in the reader's scroll. The look exists to get the page read; the structure exists to make the argument legible.

Shape: sticky top bar with scroll-spy nav → hero (eyebrow, title, typed lede, metrics) → **headline** (the answer + its caveat) → **findings** (claim cards that link to evidence) → the argument's sections → a collapsed **full log** → provenance footer. Prints to A4 on paper colours. Load **show-me** for any visual explanation and **animate-process** for an interactive mechanism figure; this skill owns the argument, scaffold, verification, and publishing.

## Act

`R=~/.agents/skills/design-doc/references`

| Goal | Command |
|---|---|
| Start an RFC / memo / sync-prep doc | `cp $R/template.html <dir>/<slug>.html`, then fill top-down ([structure](references/structure.md)) |
| Render an existing markdown report | `node $R/build-md.js <src.md> <out.html> --eyebrow="T-1 · Retro · 2026-01-01" [--title="<claim>"] --hero=hero.html [--front=front.html]` ([report mode](references/report-mode.md)) |
| Full visual sweep (every segment) | `node $R/screenshot.js <abs.html> [out-dir]` → `scroll-NN.png` |
| One capture per component | `node $R/screenshot.js <abs.html> [out-dir] --sample` → `sample-NN-<component>.png` |
| Print / pagination check | add `--print` → `doc.pdf` |
| Probe a layout bug | `node $R/inspect.js <abs.html> "<selector>"` |
| Hero thumbnail for a shared link | `node $R/thumbnail.js <abs.html> [out.png] [ratio] [--hero=<sel>]` |
| Slack cards (1600×900) | copy `$R/cards.html`, fill, `node $R/render-cards.js cards.html [out-dir]` ([share images](references/share-images.md)) |
| Draft link for a few reviewers | `gh gist create <file> --desc "<title>"` → gistpreview URL ([publishing](references/publishing.md)) |
| Publish for the org | `conjure deploy <dir-with-index.html> --site <slug> --json` ([publishing](references/publishing.md#conjure)) |

Flow, in order: **frame** the mode, claim, proof points, and limits → **verify every fact** with `rg` → **fill** the template (or build) → **sweep** and fix layout → **content passes** → **re-sweep** (height should drop) → share images and publish on request. Details per step: [structure](references/structure.md), [verify](references/verify.md).

## Detect

Use for an RFC, design doc, ADR, spec, sync-prep brief, an internal memo that sells a shipped capability with evidence, a markdown retro/measurement report that needs a shareable render, or a PR with architectural weight (≥2 reviewers, several sub-decisions, contract or ownership changes).

Skip for READMEs, ticket bodies, PR descriptions, slide decks, or anything best read as markdown.

Before styling, look for repo canon: `rg --files -g 'DESIGN.md' -g '*brand*'`. In factory-mono, `packages/core-ui/DESIGN.md` wins; the template already follows it and the Factory brand guide (`Factory-AI/factory-brand-guide`, `public/brand.json`).

## Rules

1. **Numbers survive verbatim.** Every number, id, verdict, and hedge in the page, metrics, thumbnail, and cards matches its source character for character. Never re-derive or re-round; in report mode prose passes through unchanged too. A rounded number in a card is how a caveat escapes.
2. **Voice before polish.** Load **voice** for every sentence you write (lede, headline, findings, captions, card headings). One inflated claim loses the most careful reader.
3. **Never cite an unverified constant, path, or signature.** `rg` it first; when the PR text disagrees with the code, the code wins and you flag the gap.
4. **Never write a second stylesheet or start from scratch.** `build-md.js` reads the template's styles at build time and `cards.html` mirrors its tokens; a fork drifts on the next template fix.
5. **Orange marks only what is primary or live**: the live dot, section labels, the primary bar or row, the active nav item. Never headlines, large metric values, logos, or a whole card; if everything is orange, nothing is primary.
6. **One finding is the honest limit** (`.finding.limit`, `.panel.limit`, `.callout.limit`). A wall of wins reads as marketing and costs you the other cards.
7. **Never ship without a full sweep.** The hero viewport hides failures in charts, tables, and the collapsed log; `screenshot.js` opens every `<details>` for that reason.
8. **Never publish unasked**, and never move a draft from secret gist to conjure (org-visible) without the user's go-ahead.

## Failure map

| Symptom | Action |
|---|---|
| `playwright not found` / `marked not found` | `npm i -g playwright marked && playwright install chromium` (scripts fall back to `npm root -g`) |
| Every scroll segment shows the page top | Smooth scroll froze capture; scripts inject `CAPTURE_CSS`, so check you ran the bundled `screenshot.js` |
| Blocks missing from your own capture | `.rv` blocks wait to scroll into view; capture with `reducedMotion: 'reduce'` as the bundled scripts do, or check the console for a script error |
| `dd` drops under its `dt` in a decision card | Restore `.decision dd { grid-column: 2 }` |
| Nav link highlights the wrong section | Each `nav a[href]` must match a section `id`; `--front` sections need `id` and `data-nav` |
| Reviewer says "hard to read, context implicit" | Apply the zero-context rules: [structure](references/structure.md#zero-context-rules) |
| Reviewer says "outline the key callouts" / "make it punchier" | Restructure into headline + findings, not shorter sentences: [components](references/components.md#progressive-disclosure) |
| "Unclear what happens to the old system" | Add the disposition table: [structure](references/structure.md#disposition-table) |
| Gist preview cuts off before the footer | File over ~1 MB truncated by the gist API: [publishing](references/publishing.md#size-budget-first), or deploy to conjure |
| Shared link shows no preview card | Expected for both gistpreview and conjure (SSO); post the thumbnail or cards: [publishing](references/publishing.md#no-link-previews) |
| `render-cards.js` warns about overflow | Cut rows; never shrink type below the template sizes |

## References

Load on demand; do not reabsorb into this file.

- `references/structure.md`: modes and their spines, the source-of-truth pass, fill order, zero-context rules, disposition table, insertion knock-ons, content passes, decision-card and "punchier" traps, citing code.
- `references/components.md`: visual system and type scale, progressive disclosure (headline → findings → story → full log), metrics and charts, motion, the component inventory.
- `references/verify.md`: the sweep loop, which sweep when, bugs only a capture shows, re-verification, the pre-share checklist.
- `references/report-mode.md`: rendering markdown sources with `build-md.js`, `--front` curation, changes-and-impact tables.
- `references/share-images.md`: hero thumbnail contract and Slack card archetypes.
- `references/publishing.md`: secret-gist drafts, conjure sites, size budget, update flows, dead ends.
- `references/template.html`: the scaffold and the one stylesheet; `cards.html`: card skeletons on the same tokens.
- `references/*.js`: `build-md`, `screenshot`, `inspect`, `thumbnail`, `render-cards`; shared resolution and args in `lib.js`.
- `../show-me/references/surfaces.md`: rendering and embedding visual explanations (load through **show-me**).
