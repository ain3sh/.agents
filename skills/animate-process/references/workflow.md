# Workflow: from concept to a verified figure

## The one idea

**The object is the explanation.** Don't draw boxes, arrows, and labels. Invent
a real, well-made physical thing whose working *is* the concept. How earlier
figures mapped:

| Concept | Object |
|---|---|
| One shared GPU context serving many canvases | A gantry plotter: one print head visiting 16 wells |
| A cache key that skips work when nothing changed | A pin-tumbler lock: when every pin matches, the plug turns and nothing is redrawn |
| Seven render targets with different bytes per texel | A chest of seven drawers, each as deep as its bytes |
| A separable blur (49 × 49 taps vs 49 + 49) | A bed-of-nails stamp beside two combs on rails |
| A spring that presses and leans | A test rig with springs, a probe and a dial gauge |
| A height profile | A profile (contour) gauge pressed against the edge |
| Light that depends on facing | A small photo studio: key and fill lamps around a turntable |

Two ways this fails, both seen in practice:

- **Too abstract.** Stacked plates, floating slabs, or labelled boxes don't read
  as anything.
- **Too flat and bland.** One big slab with a few lines on it has no volume, no
  parts, and nothing to discover.

The fix for both: a recognisable machine, built from many small, precise,
purposeful parts.

**Every creation is highly detailed**, however small the idea or the request:
a quick explainer is still a dense, real machine. What scales with the size is
how far you push it: a Figure gets the 4× sweep over its subject and mechanism,
a Hero or an Epic over the whole drawing.

- **Read the real thing.** Build it the way the real object is built: every
  screw, seam, bevel, bushing, label plate, cable with its connector, scale with
  its ticks, and the parts that hold the parts.
- **Two looks.** At 1× it reads as one clear machine. At 4× every region still
  has something true to find; a bare face or an empty corner is unfinished work,
  not calm.
- **Purposeful, never noise.** Detail comes from parts that belong to the
  mechanism. Each one sits on another part, ends on an edge, and fades rather
  than stops.
- **Check it last.** Before finishing, zoom to 4× and add the real parts that
  are missing wherever a region is plain.

## Workflow

Write the concept and the parts list before any geometry; most of the quality
is decided there.

1. **Size it.** Name the size before any other work.
   - **Figure**: one mechanism, 40–80 parts, SVG with at most one WebGL layer.
     Build it without asking and don't quote a time (it often finishes well
     under an hour); budget up to an hour for the progress checks.
   - **Hero**: a dense object, several WebGL layers, 80–150 parts. About 2–4
     hours. Say so, then build it unless the user asked for something quick.
   - **Epic**: a whole vehicle, building, or plant with many moving systems. 6
     hours or more. Don't start it: give the estimate, propose a Hero that keeps
     the core of the idea, list what the full version would add, and build the
     Epic only when the user chooses it.
   - Have a working page in the browser within the first hour and deepen it
     from there. Run `date` at the start and at each step; when a step runs past
     twice its share of the estimate, tell the user where it stands.
2. **Truth first.** Collect the real numbers and behaviour of the thing being
   explained: sizes, counts, thresholds, curves. The readout, motion, and
   caption must all be true. Write the model as a small pure module (like
   `rig.ts` in the test-rig example) and drive everything from it.
3. **Invent the object.** Pick a machine, tool, instrument, or piece of
   furniture whose mechanism maps one-to-one onto the concept. Say in one
   sentence what moves and what that motion means. Never copy a reference
   image: take its finish, not its object.
4. **Parts list.** At least 40 parts (40–80 for a Figure, 80–150 for a Hero),
   grouped: base (plate, feet, groove, corner screws, label plate, ruler strip),
   structure (posts, rails, frame bars, end stops), mechanism (carriage,
   bushings, springs, plunger, needle), controls (knurled knob, thumb screw,
   crown), and the subject, the one lit part. Each part sits on another part.
   [craft](craft.md), section 3, has a parts vocabulary with recipes.
5. **Plan the world.** World units of about 1 px of the real thing: x and y on
   the floor, z up. Lay out plans as rounded rectangles `{x, y, w, d, r}` and
   circles. Camera: azimuth 45° by default, 35–60° to show the long side,
   elevation 30° (higher, like the ripple tank's 44°, to look into something
   open). Fit with `fitProjection(points, width, height, { pad, azimuth })`.
6. **Build geometry once.** Precompute every static path with the kit:
   `slabOf`, `cylinder`, `extrude`, `planOutline`, `topTicks`, `knurl`, `coil`,
   `radialTicks`. Round parts on any axis come from `kit/lathe.mjs`, pipes and
   cables from `kit/tube.mjs`. Moving parts are built once at rest and moved
   with `translateAlong`; only parts whose shape changes are rebuilt per frame.
7. **Paint back to front, bottom to top.** Sort repeated parts with `depthOf`.
   Split anything that wraps another part into back and front halves (springs
   around a rod, frame bars around a carriage). A moving part is drawn in the
   slot where it physically sits ([craft](craft.md), section 5). Once a figure
   has pipes, cables, and round parts, stop tuning keys by eye: record each
   item's shape with `A.recorder(P, { order, spring })`, let `A.settle(R, P)`
   set the keys from measured depth, and end the build with
   `A.auditOrExit(R, P)`. Route pipes before drawing them: real ports at both
   ends, legs along the structure, crossings on straights, collars gapping the
   pipe ([craft](craft.md), section 8). A rod sliding out of a gland is one rod
   from `G.rodOut`, recorded with `A.slide`.
8. **Frame it.** A card: `Fig n` top left, a short title top right, the
   interaction hint bottom left, the live readout bottom right
   (`plateHtml`). Legend keys and a true caption go under the card; words stay
   out of the drawing apart from at most one tiny engraved label.
9. **Make it live.** Calm, time-based motion: exponential follow or real
   springs. An idle tour loops when nobody touches it; the figure responds to
   pointer and keyboard, stops offscreen, and goes still under reduced motion.
   Write attributes on refs; don't re-render per frame ([motion](motion.md)).
10. **Verify like a critic.** The owner finds faults by zooming in, so zoom in
    first and read every PNG.
    - Capture desktop, phone (390 wide), hover, and several moments of motion
      with `capture.mjs`; use `drive.mjs` for sequences, the apart pose, and the
      `--no-webgl` fallback.
    - **Audit to zero.** With pipes, cables, or round parts, `node build.mjs
      --audit` must end `audit passed`, every failing line at 0.
    - **Line check to zero.** The audit never sees line markup: `lines.mjs` on
      the dark and `-light` pages, and in every resting pose via `drive.mjs`'s
      `["lines"]` action, must print `line ends: 0`.
    - **4× close-ups of every junction in both themes**, assembled and apart:
      flanges, tees, elbows, clamps, valves, bellows, bands, saddles, ball
      joints, crossings, every curved body (no tone staircase), every texture
      end, every sliding rod at rest and full stroke, every window with text or
      shader content.
    - **Shaders**: a contact sheet slowed with `["slow", 0.05]` across every
      transition; nothing pops, no colour switch, edges read 0. In light, log
      ink per frame through each transition ([verify](verify.md),
      "Light-theme shaders").
    - Put your PNG next to the examples and ask: is it instantly a real object,
      rich in small parts with volume, every line ending on something,
      rewarding at 4×? Iterate until yes. Checklist: [verify](verify.md).

## Examples

Each framework-free example builds with `node build.mjs` (add `--light`),
writing a standalone page next to the script. Built pages and PDFs are not
shipped; build them to look.

- `dial-indicator/`: the smallest, a dial gauge on a stand, about 300 lines.
- `desk-computer/`: a desk computer with a keyboard you can type on; the typed
  line appears on a CRT drawn in the plane of the case front, which collapses to
  a line and a dot when switched off. About 85 solids and 850 paths.
- `push-button/`: a spring-loaded push button that closes a circuit and lights
  a bulb; the reference for a PDF link on the card (`pdfButton`) and a
  `sheet.mjs` for print.
- `arcade-cabinet/`: an upright cabinet with its side panel off, a Hero of
  about 240 solids and 15 cables. A coin rolls down the chute at the speed a
  disc reaches on a 30° slope, trips the switch wire, and the pulse runs along
  its cable to the board; the CRT warms up and runs an attract mode in the
  plane of the tilted monitor. Shows camera placement for a cutaway, a concave
  board as a prism along any axis, moving parts rebuilt in the page from the
  build's module, and live items in reserved slots of the settled order.
  `--audit` proves it.
- `raptor-engine/`: a rocket engine in a test stand. Round parts from
  `lathe.mjs`, pipes and harness from `tube.mjs`; it comes apart into 11
  assemblies with staggered springs and per-frame depth re-sorting, and the
  audit proves at rest, apart, and in every replayed frame that nothing passes
  through anything. A WebGL plume, shock, splash, and steam render between the
  back and front SVG. The reference for dense pipework, smooth shading, fades,
  and shader quality.
- `ripple-tank/`: a school ripple tank seen from 44° up. Two WebGL layers
  (lamp light, shadows, and caustics on the paper; the water's reflections and
  glass) registered to the isometric planes and driven by a pure dispersion and
  optics model (`model.mjs`).
- `test-rig/`: a production figure (React/Next): a glass button on a
  spring-mounted carriage, a finger probe that presses and pulls, a dial gauge
  reading the lean. 53 solids, about 470 paths. The quality bar for the drawing.
- `spot-plate/`: a second production React figure: six pairs of glass drops,
  each pair from one distance field, merging when closer than `merge`; a fan of
  feeler blades sets it. The reference for morphing shapes and one control
  driving many parts.

## Setup paths

- **Standalone HTML, a static SVG, or any non-React site**: a Node build script
  like `examples/dial-indicator/build.mjs`. Import `kit/iso-kit.mjs`, assemble
  strings with `solidSvg`, `lineSvg`, `dotsSvg`, `wireSvg`, `faceTextSvg`, wrap
  with `figureSvg` and `plateHtml`, and write the page with
  `pageHtml({ script: kitScript() + live })` (`+ glScript()` with a shader). For
  a lone `.svg`, `figureSvg({ standalone: "dark" | "light" })` embeds the styles.
- **React or Next.js**: copy `kit/` into the project (e.g. `components/iso/`),
  keep geometry in plain `.ts` modules, build static art in a server component
  with the `draw.tsx` components, and pass it to one `"use client"` live
  component ([react](react.md)).

## Embedding in a design doc

The kit's tokens match the design-doc template (Tungsten greys, orange `lit`,
Geist), so a plate drops into a design-doc page without restyling. Emit a
fragment from the build script instead of a page:

```js
import { writeFileSync } from "node:fs";
writeFileSync(join(HERE, "fragment.html"),
  `<style>${k.ISO_CSS}</style>\n<div class="iso" data-theme="dark">${body}</div>\n` +
  `<script type="module">${(kitScript() + live).replace(/<\/(script)/gi, "<\\/$1")}</script>\n`);
```

- Paste it into a section of the doc (or a `build-md.js --front` fragment)
  as-is. Don't wrap the plate in `figure.diagram`: the plate is its own card,
  and a second frame around it reads as a box in a box.
- Include `ISO_CSS` once per page, however many figures.
- The examples' live code queries `document` (`.iso-stage`, `[data-readout]`);
  with two or more figures on a page, scope every query to the figure's own
  `.iso` root, or one figure drives the other.
- Never scrape a built page for its body: the inlined kit source contains
  `pageHtml`'s own `<main>` markup, so a regex grabs half a script.
- Check it with the design-doc sweep (`screenshot.js --sample` captures
  `.iso-figure`) and with this skill's `capture.mjs` on the doc for motion.
