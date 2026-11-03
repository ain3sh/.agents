# Animating a sheet

Turn a finished sheet into a ~10 s film: lines draw themselves in, the camera pulls back, layers lift into an exploded view, the full sheet resolves. It reads like a pen drawing the sheet while a camera moves over it. Same rules as the drawing: monochrome, slots not content, variable codes, unbranded.

Start from `motion/scene-dialog.js` + `motion/base.css`. It is the reference film (11 s, 1920×1080, 60 fps). Adapt it; do not start blank.

## Render

Playwright opens `motion/player.html`, calls the scene's `render(t)` for every frame, screenshots it, and pipes the PNGs into ffmpeg. Needs Node 18+, ffmpeg on `PATH`, and `playwright` installed in the **current directory** (the scripts resolve it from `cwd`, never from the skill folder).

```bash
K=~/.agents/skills/dimensional-drawing/motion
mkdir -p <work> && cd <work> && npm install playwright && npx playwright install chromium

node $K/render.mjs --scene $K/scene-dialog.js --css $K/base.css --out dialog.mp4          # the reference film
node $K/render.mjs --scene $K/scene-dialog.js --css $K/base.css --still 6.6 --out f.png   # one frame, to check a beat
```

| flag | default | |
|---|---|---|
| `--scene` | required | scene file (`kit.scene(id, { init, render })`) |
| `--css` | none | stylesheet for the stage (`motion/base.css`) |
| `--out` | `out.mp4` | MP4, or PNG with `--still` |
| `--duration` | `11` | seconds |
| `--fps` | `60` | 30 renders twice as fast |
| `--width` / `--height` | `1920` / `1080` | stage size |
| `--bg` | `#ffffff` | background |
| `--id` | first scene | scene id when the file registers several |
| `--still <t>` | | render a single frame at time `t` |
| `--crf` | `16` | x264 quality (lower = bigger, sharper) |
| `--ffmpeg` | `ffmpeg` | path to ffmpeg |

Set `CHROMIUM_PATH` to use an existing Chrome/Chromium instead of the downloaded one. The page asks Google Fonts for Arimo; offline it falls back to Helvetica/Arial (same metrics). Measured: the 11 s reference at 30 fps renders in about 25 s.

The scene only needs the tiny `kit` in `player.html` (`seg, lerp, eo, ei, eio, clamp01, stage, h, css, scene`) and must be a **pure function of time**: `render(t)` sets every property from `t` alone, never from the previous frame. That is what lets the renderer jump to any frame. Other animation libraries (Remotion, Motion Canvas, GSAP, Lottie…) are not tested; porting is possible because the scene is pure, but check the library's license first (Remotion needs a company license above 3 people).

## Choreography (reference timing, seconds)

Scene time is scaled with `t = t / 0.85`, so the numbers below run about 15 % faster on screen. Change that one factor to speed up or slow down the whole film.

1. **0 – 2.3 · Close-up on the header.** Camera at ~4.4× on the top-left of the plan. The outer border draws from the top-left corner, then the lead circle, the X-box, the title slot, the header divider, then the header dims (S1, Z1, S5, H1). Tiny drift (z 4.4 → 4.2) keeps it alive.
2. **2.3 – 4.2 · Pull back to the plan view.** Log-zoom to ~1.7×. While moving, the rest of the plan draws: trail control, body well, content slots, label/value slots, footer actions, centerlines, chained dims top/bottom/left/right, radius callouts, boxed notes, detail circles, view title.
3. **4.2 – 7.2 · Layers lift.** The camera eases left to where the exploded view lives. Copies of container → body → slots morph from the flat plan matrix to the axonometric matrix and rise to their z. **Strokes first, fills after** (fills fade in from `a+0.55` to `a+1.25`); without that a white fill flashes over the drawing. Static bottom layers (viewport, scrim, shadow) draw in under them; leaders and layer labels follow.
4. **7.2 – 9.2 · Pull back to the full sheet.** Zoom to 1.0. The sheet border draws, then notes, tables and the detail views (header controls, footer actions, viewport placement, nested corner, field, radius details) each draw in a 0.3–0.5 s burst.
5. **9.2 – end · Hold.** Very slow push (z 0.998 → 0.988) so the last frame is not dead.

Total ~11 s. Keep films 8–15 s.

## How the template works

- **One SVG, one camera.** The sheet is drawn once in `init` at `viewBox 0 0 1900 1060` (wider than the 1700 drawing so the final frame fills 16:9 with no side gutters). A wrapper `.dw-cam` gets `translate(960 − cx·z, 540 − cy·z) scale(z)` from camera keys `DW_CAM = [{t, cx, cy, z}]`, interpolated with ease-in-out and **log zoom** (`exp(lerp(log z0, log z1, p))`), so zooms feel even.
- **Registration.** Call `at(start, stagger, dur)` before drawing a group. Every element made by `mk()` after it gets a window `[start + i·stagger, … + dur]`. Group elements in drawing order: outline → structure → slots → dims → labels.
- **Two kinds of element.**
  - `d` (drawn): solid strokes. `pathLength=1`, `strokeDasharray: 1 2`, `strokeDashoffset: 1 → 0` with ease-in-out; fill fades in over the last 45 %.
  - `f` (faded): text, dashed slots, centerlines, envelopes, hatches. Opacity with ease-out. Dashed lines can't use the dash trick, so they fade.
- **Morph groups.** `mg(z, start)` makes a group that lerps its matrix from `flat = [k,0,0,k,PX,PY]` (the plan) to `iso = [.94s,.17s,−.34s,.47s,TX,TY]` and subtracts `z·v` from ty. Set `--u = 1/√|det M|` each frame so stroke widths stay constant while the group scales.
- **Performance.** Values are quantized to 1/400 and skipped when unchanged; fills of morph groups are queried once.

## Adapting to a new component

1. Copy the drawing sheet's geometry (plan origin `PX, PY`, scale `k`, the `r()/dimH()/dimV()/rad()/nb()/detailRef()/table()/notes()` calls) into `init`, keeping the template's helpers.
2. Rewrite the `at()` timeline for the new plan: open on its most characteristic corner (header, handle, notch), let the rest of the plan draw while pulling back.
3. List the layers for the exploded view (bottom static ones with `G(z)`, lifting ones with `mg(z, start)`), 0.1 s apart.
4. Retarget `DW_CAM`: close-up → plan center → exploded center → sheet center (`950, 530`, z ≈ 1).
5. Check frames at the key beats with `--still` (0, 1.2, 2.4, 3.3, 4.6, 5, 5.9, 6.6, 8, 10, 11 s scene time). Look for: elements popping instead of drawing, fills flashing, labels outside the frame mid-move, a busy first second.
6. Render the MP4 (`--fps 30` for a quick check, 60 for delivery).

## Style rules for motion

- One thing leads at a time: the eye follows the pen. Dims come after the geometry they measure; labels after their leaders.
- Ease-in-out for camera and strokes, ease-out for fades. No bounce, no overshoot, no color.
- Background white, ink `#111`, grays only. Arimo/Helvetica caps lettering, same sizes as the sheet.
- No music or voice unless asked.

Reply in one or two sentences with the film's length and what each beat shows.
