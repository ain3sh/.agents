---
name: dimensional-drawing
description: "Draw a UI component or physical product as an Apple-style monochrome dimensional spec sheet with variable-coded dimensions, optionally animated into a short MP4. Use for anatomy, spec sheet, redline, or dimensional drawing requests."
---

**Draw one subject the way Apple's accessory dimensional drawings do** (developer.apple.com/accessories/dimensional-drawings): everything on one sheet, notes top-left, views spread across the sheet with smaller detail views, tables beside the views that use them; every dimension a variable code, no copy, no color, no brand. Output is one self-contained HTML file, and on request a ~10 s MP4 of the sheet drawing itself.

## Act

`K=~/.agents/skills/dimensional-drawing`. Never start blank: copy the closest example and its inline drawing kit. Playwright is resolved from the **current directory**, so work in a scratch dir, never inside `$K`:

```bash
mkdir -p <work> && cd <work> && npm install playwright && npx playwright install chromium
```

| Goal | Do |
|---|---|
| Sheet for a UI component | `cp $K/examples/card-sheet.html <name>-sheet.html` (or `dialog-sheet.html`); measure the real source; rewrite title block, notes, plan, exploded layers, details, tables ([drawing](references/drawing.md)) |
| Sheet for a physical product | Same kit: third-angle views + section A–A, mm, published specs only ([drawing](references/drawing.md#component-specific-views-pick-what-applies)) |
| Check the sheet | `node $K/scripts/shot.mjs <name>-sheet.html --out <name>.png`; read the PNG for overlapping labels and border crossings, fix in one pass |
| Animate it | Load [motion](references/motion.md); copy `$K/motion/scene-dialog.js`, retarget it, then `node $K/motion/render.mjs --scene <scene>.js --css $K/motion/base.css --out film.mp4` |
| Check one beat | `node $K/motion/render.mjs --scene <scene>.js --css $K/motion/base.css --still 6.6 --out frame.png` |

Pick the example by shape: `card-sheet.html` (flexible width, body well, nested corner, shadow envelope) or `dialog-sheet.html` (fixed width, scrim, viewport placement, header controls, footer actions).

Flow: read the source → measure every instance → assign codes → title block → plan view → exploded layers → details → tables → render and read → deliver. Reply in one or two sentences: what was drawn and the `[TBD]` values the team should define.

## Detect

Use when asked for an anatomy, spec sheet, redline, or dimensional drawing of a component, screen, or device, or to animate one. Use **animate-process** for a mechanism explained as a machine, **show-me** for box-and-arrow diagrams.

Needs Node 18+, Playwright with Chromium (installed in the work dir as above, or `CHROMIUM_PATH`), and ffmpeg on `PATH` for MP4.

## Rules

1. **Never add color.** Black line on white paper, grays only, `color-scheme: light`; tell things apart by line weight, dash pattern, hatch and light gray fill. A hex outside the gray tokens is a defect.
2. **Never draw content.** Slots, not copy: `TITLE SLOT · FLEX`, `ACTION · HUG`, `CONTENT SLOT · FILL`. A text-width dimension goes stale the moment the copy changes.
3. **Never write a bare number on the drawing.** Every dimension is a code; the tables give code, variable, value; derived values are formulas with the result (`R2 = R1 − B − S6 = 11`). A code missing from a table or a formula that does not close is unfinished.
4. **Never brand.** No product or company names, logos or wordmarks in drawing, title block or footer unless asked; use `UI-CARD-001`, "UI component reference".
5. **Never invent a value.** Anything not in the source (viewport margin, overflow behavior, unpublished physical dims) is `[TBD]`, drawn as a proportional schematic; a guessed margin gets built.
6. **Never make `render(t)` depend on the previous frame.** The renderer jumps to arbitrary frames; stateful scenes render garbage stills.
7. **Never deliver unseen.** Render the sheet at 1800 px and the film's key beats, read the images, fix overlaps and border crossings first.

## Failure map

| Symptom | Action |
|---|---|
| Hatched shape renders solid | Its class sets `fill`; give hatched shapes a class without one ([pitfalls](references/drawing.md#pitfalls)) |
| Strokes thicken inside the exploded view | `vector-effect: non-scaling-stroke`; fills via `style`, not attributes ([pitfalls](references/drawing.md#pitfalls)) |
| Labels collide in a tight chain or run into a table | Stagger with `dx`/`dy`; anchor `end` at the feature ([pitfalls](references/drawing.md#pitfalls)) |
| White fill flashes over the drawing while layers lift | Strokes first, fills `a+0.55 → a+1.25` ([motion](references/motion.md#choreography-reference-timing-seconds)) |
| Film too fast or slow overall | Change the single `t = t / 0.85` factor ([motion](references/motion.md#choreography-reference-timing-seconds)) |
| `playwright not found` | `npm install playwright` in the current directory, then `npx playwright install chromium` |
| `ffmpeg not found on PATH` | `apt`/`brew`/`winget install ffmpeg`, or pass `--ffmpeg /path/to/ffmpeg` |
| Sheet or film lettering looks off | Arimo loads from Google Fonts; offline falls back to Helvetica/Arial (same metrics) |

## References

Load on demand; do not reabsorb into this file.

- `references/drawing.md`: code system, page structure, sheet layout, component-specific views, measuring a UI component, the SVG kit API and conventions, pitfalls, the pre-delivery checklist.
- `references/motion.md`: render.mjs flags, choreography beats, how the template works, adapting the scene to a new component, motion style rules.
- `examples/`: `card-sheet.html`, `dialog-sheet.html`, the two reference sheets with the drawing kit inline.
- `motion/`: `render.mjs`, `player.html`, `base.css`, `scene-dialog.js`, the headless renderer and the reference scene.
- `scripts/shot.mjs`: full-page screenshot of a sheet at a given width.
