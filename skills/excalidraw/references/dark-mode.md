# Dark-mode rendering

**Dark output is a render-time concern, not an authoring concern.** `excalirender --dark -s 2` applies Excalidraw's own theme inversion to a file that was authored in light colors. Your `.excalidraw` source stays light; the PNG comes out dark.

## What `--dark` actually does

It runs every element's color through Excalidraw's light-to-dark theme mapping at render time:

- Light canvas (`#ffffff`) -> near-black
- Pastel fills (`#a5d8ff`, `#b2f2bb`, `#ffd8a8`, ...) -> matching dark variants
- Dark text/stroke (`#1e1e1e`) -> light

The source file is untouched. One file, two possible outputs:

```bash
excalirender diagram.excalidraw -o light.png -s 2          # light output
excalirender diagram.excalidraw -o dark.png --dark -s 2    # dark output (our default)
```

## Failure modes (what droids keep doing wrong)

All four of these produce a **broken, washed-out, double-inverted** render when combined with `--dark`:

- **Pre-colored dark fills** -- e.g. `#1e3a5f`, `#1a4d2e`, `#2d1b69`, `#5c3d1a`, `#5c1a1a`, `#1a4d4d`. `--dark` inverts them *again*, producing washed-out pastel shapes on a pale-gray canvas. Use the pastel palette in `colors.md` and let `--dark` do the mapping.
- **`"viewBackgroundColor": "#1e1e2e"`** (or any dark hex). `--dark` inverts the canvas, so a dark source background renders as pale gray. Keep it `#ffffff` or omit.
- **Light text colors in the source** -- e.g. `#e5e5e5`, `#a0a0a0`. They become dark after inversion, invisible on the rendered dark canvas. Use `#1e1e1e`.
- **Full-canvas background rectangle element** -- inflates the scene bbox, so the PNG balloons with the real diagram as a speck. `--dark` inverts its fill to pale gray on top of that. Just don't add it.

## The whole rule

One source file in light theme; pass or drop `--dark` at render time to pick the output theme. Don't try to "compose" dark mode across the source and the flag -- you'll collide with Excalidraw's own inversion.
