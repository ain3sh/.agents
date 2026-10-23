---
name: animate-process
description: "Build an interactive isometric SVG figure that explains a process, algorithm, or system as a working physical machine, in Factory's theme, with optional WebGL effects and A4 print sheets. Use for explainer figures in docs, posts, or design docs, even when nobody says isometric."
---

**The object is the explanation**: invent a real, well-made machine whose working *is* the concept, build it from many small precise solids with a kit that projects, shades, orders, and proves the geometry, and drive every moving part and every number from one true model.

## Act

`K=~/.agents/skills/animate-process`. Work in a figure directory, never inside the skill: link the kit beside it so the examples' `../../kit` imports resolve.

```bash
mkdir -p <work>/figures && ln -s $K/kit $K/scripts <work>/
cp -r $K/examples/<closest> <work>/figures/<name> && cd <work>/figures/<name>
```

| Goal | Command (from the figure directory) |
|---|---|
| Build the page | `node build.mjs` → the page named in its final `writeFileSync` (rename it when adapting an example); `--light` for the light page |
| Prove the geometry (pipes, cables, round parts) | `node build.mjs --audit` → must end `audit passed` |
| Line-end check | `node ../../scripts/lines.mjs <name>.html --out shots/lines.png` → `line ends: 0` |
| Screenshot, phone, hover, close-up | `node ../../scripts/capture.mjs <name>.html --out shots/a.png [--width 390] [--hover 0.6,0.5] [--zoom x,y,w,h] [--theme light]` |
| Sequences, slow motion, contact sheets, no-WebGL fallback | `node ../../scripts/drive.mjs <name>.html '[["slow",0.05],["sheet","shots/s.png",50,12]]' [--no-webgl]` |
| A4 / Letter PDF (poster, drawing, detailed) | write `sheet.mjs`, then `node ../../scripts/print.mjs sheet.mjs --format all --png` ([print](references/print.md)) |
| Embed in a design-doc page | emit a fragment instead of a page ([workflow](references/workflow.md#embedding-in-a-design-doc)) |
| React / Next.js | copy `$K/kit` into the project ([react](references/react.md)) |

Pick the closest example first: `dial-indicator` (smallest, ~300 lines), `desk-computer` (keyboard and CRT), `push-button` (with print sheets), `arcade-cabinet` (dense Hero, cutaway, cables), `raptor-engine` (pipework, explode, WebGL plume: the shader bar), `ripple-tank` (two WebGL layers from a physics model), `test-rig` (React; the drawing bar), `spot-plate` (React; morphing shapes). Descriptions: [workflow](references/workflow.md#examples).

Flow: **size** it → collect the **truth** → invent the **object** → **parts list** (40+) → plan world and camera → **build geometry once** → **paint back to front** → frame it in a card → make it **live** → **verify like a critic**. Each step: [workflow](references/workflow.md#workflow).

## Detect

Use when a mechanism, algorithm, pipeline, or system needs explaining and a working machine would carry it: docs, posts, landing pages, a design doc. Use **show-me** instead for box-and-arrow diagrams, charts, and code companions.

Needs Node 20.10+ and Chrome or Chromium: `CHROME_PATH`, system installs, then `~/.cache/ms-playwright` (the global `playwright install chromium` covers it).

## Rules

1. **Never draw boxes, arrows, and labels.** Too abstract (floating slabs) and too flat (one slab with lines) both fail; a recognisable machine of many small, purposeful parts fixes both.
2. **Truth before geometry.** Every number in the readout, motion, and caption comes from one pure model module; never tune a number by eye.
3. **Size before building.** Figure: 40–80 parts, build without asking, no time quote. Hero: 80–150 parts, about 2–4 hours, say so. Epic: 6 hours or more, never start it; propose a Hero and list what the full version adds. A working page opens within the first hour; run `date` per step and report when a step runs past twice its share.
4. **One `lit` part, in Factory orange.** Base `lo`, structure `mid`, subject `hi`, grooves `faint`. Colour only when colour is the subject; a new colour takes the nearest Tungsten step ([craft](references/craft.md), sections 4 and 7).
5. **Every line ends on something, nothing passes through anything, every crossing is in true depth order**, proved by `--audit` and `lines.mjs`. Fix interlocks in the geometry, never with a key bias or a stand-in shape (the audit fails those).
6. **Shaders never pop or cut off**: envelopes on every uniform, crossfades driven by the physical quantity, world space in the figure's camera, every term at zero before a bound; the SVG must still read without WebGL. Read [webgl](references/webgl.md) before writing one.
7. **Read every PNG you make**, at 4× over every junction, in both themes, assembled and apart. Highly detailed at 1×, still rewarding at 4×: a bare face or empty corner is unfinished work.

## Failure map

| Symptom | Action |
|---|---|
| `No Chrome found` | `playwright install chromium`, or set `CHROME_PATH` |
| Audit lists clearance, terminal, fold, wobble, or depth failures | [verify](references/verify.md), "Audit" table: each line's cause and fix |
| `line ends: N` | [verify](references/verify.md), "Line ends"; read the ringed PNG |
| Tone staircase on a curved body | Smooth knots, an analytic `slope`, `G.bandsOf` ([kit](references/kit.md), section 10) |
| Shader pops, colour switches, or edges read above 0 | [webgl](references/webgl.md), section 7 |
| Page dies with a SyntaxError after inlining | Live code redeclared `smooth`, `burst`, or `settle` ([kit](references/kit.md), section 8) |
| Large React page logs key warnings | [react](references/react.md), the large-page trap |
| Embedded figure doesn't move, or moves another figure | Scope live queries to the figure's own root; one `ISO_CSS` per page ([workflow](references/workflow.md#embedding-in-a-design-doc)) |

## References

Load on demand; do not reabsorb into this file.

- `references/workflow.md`: the one idea and object mapping, sizes, the ten steps, examples, framework-free vs React setup, embedding in a design doc.
- `references/craft.md`: the look in depth: parts vocabulary with recipes, tones, painter's order, camera, themes, round parts and pipes, exploded views, screens on faces, anti-patterns. Read before designing.
- `references/kit.md`: the API with signatures (`kit/iso-kit.mjs`, `lathe.mjs`, `tube.mjs`, `audit.mjs`, `gl.mjs`, React components, tools).
- `references/motion.md`: loops, springs, tours, pointer, keyboard, reduced motion, envelopes, exploded views, depth re-sorting.
- `references/verify.md`: `capture.mjs` and `drive.mjs` usage, line ends, the audit table, close-ups, light-theme shaders, the review checklist, common faults.
- `references/webgl.md`: shaders inside the drawing: layer stack, camera contract, ray-marching, API, craft rules, light theme, verification.
- `references/print.md`: A4 and Letter sheets from a built figure.
- `references/react.md`: the server/client split for React and Next.js.
- `references/walkthrough.md`: how the test rig was designed, concept to code.
- `NOTICE`: upstream source and what this copy changed.
