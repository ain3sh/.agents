---
name: excalidraw
description: Create hand-drawn style diagrams using Excalidraw JSON format. Generate .excalidraw files for architecture diagrams, flowcharts, sequence diagrams, concept maps, and more. Files can be opened at excalidraw.com or uploaded for shareable links via scripts/upload.py.
---

# Excalidraw Diagrams

Create diagrams by writing standard Excalidraw element JSON and saving as `.excalidraw` files. These files can be drag-and-dropped onto [excalidraw.com](https://excalidraw.com) for viewing and editing. No accounts, no API keys, no rendering libraries -- just JSON.

## Defaults you must apply

- **Dark mode is the default.** Every diagram ships with a full-canvas dark background rectangle as element 0 (see `references/dark-mode.md`) and dark-mode fills/strokes. Only drop dark mode if the user explicitly asks for light -- never "because it's simpler".
- **Always render to PNG with `excalirender`** before shipping a diagram anywhere a human will read it (PR body, Slack, docs, Notion). An editable-link on its own is not a deliverable -- GitHub, Slack, and most doc surfaces will not inline-render it.
- **Always render at `-s 2`** (2x scale). 1x looks mushy on retina displays.

The canonical render command, which you should be able to type from memory:

```bash
excalirender diagram.excalidraw -o /tmp/diagram.png --dark -s 2
```

## Workflow

1. Write the elements JSON -- an array of Excalidraw element objects (element 0 = dark background rect).
2. Save the file as `.excalidraw` wrapped in the envelope below.
3. Render to PNG with `excalirender --dark -s 2`.
4. Embed the PNG (via `gh-attach` for GitHub, or direct upload for Slack/Notion).
5. Optionally upload the raw `.excalidraw` for an editable companion link tucked in a `<details>` block.

### Saving a diagram

Wrap your elements array in the standard `.excalidraw` envelope:

```json
{
  "type": "excalidraw",
  "version": 2,
  "source": "droid",
  "elements": [ ...your elements array here... ],
  "appState": {
    "viewBackgroundColor": "#1e1e1e"
  }
}
```

### Uploading for a shareable link

```bash
uv run --with cryptography python ~/.agents/skills/excalidraw/scripts/upload.py diagram.excalidraw
```

Uploads to excalidraw.com (no account needed) and prints a shareable URL.

**Note:** This produces a shareable *editing* link, not an embeddable image. GitHub markdown will not render it inline -- it's just a clickable URL. Use the rendering workflow below to get an inline image.

### Rendering to PNG/SVG (excalirender) -- required step

Use `excalirender` to render `.excalidraw` files directly to PNG, SVG, or PDF without a browser. This is not an optional polish step -- a diagram that never gets rendered to PNG does not count as delivered.

**Install** (native Linux binary, no dependencies):
```bash
curl -fsSL https://raw.githubusercontent.com/JonRC/excalirender/main/install.sh | PREFIX=$HOME/.local sh
```

**Render.** Dark mode at 2x is the default on every command -- deviate only when the user explicitly requests otherwise:

```bash
excalirender diagram.excalidraw -o output.png --dark -s 2   # DEFAULT -- use this
excalirender diagram.excalidraw -o output.svg --dark -s 2   # SVG, dark mode
excalirender diagram.excalidraw --transparent --dark -s 2   # Transparent, dark (overlays)
excalirender diagram.excalidraw -o output.png -s 2          # Light mode -- only when explicitly requested
```

If you catch yourself typing `excalirender` without `--dark -s 2`, stop and add both flags.

### Embedding in GitHub PRs

To get a diagram rendering inline in a PR body on GitHub:

1. Create the `.excalidraw` file
2. Render to PNG: `excalirender diagram.excalidraw -o /tmp/diagram.png --dark -s 2`
3. Upload to GitHub CDN via `gh-attach`: `gh-attach --repo owner/repo --md /tmp/diagram.png`
   - This prints a markdown image link with a `user-attachments.githubusercontent.com` URL
   - Use this URL in the PR body: `![Diagram](https://github.com/user-attachments/assets/...)`
4. Optionally upload an editable link: `uv run --with cryptography python ~/.agents/skills/excalidraw/scripts/upload.py diagram.excalidraw`
5. Put the editable link in a collapsible section directly below the image so it's visually attached to the diagram:

```markdown
![Architecture](https://github.com/user-attachments/assets/...)

<details>
<summary>Edit diagram</summary>

Source: https://excalidraw.com/#json=...

Rendered with: `excalirender diagram.excalidraw -o /tmp/diagram.png --dark -s 2`

</details>
```

**Do NOT:**
- Commit the PNG to the branch -- use `gh-attach` for hosting
- Use `raw.githubusercontent.com` URLs -- they 404 on private repos
- Put the Excalidraw edit link as a bare clickable link -- it shows a scary "Loading external drawing will replace your existing content" warning to anyone who clicks it

**If `gh-attach` has no browser cookies** (e.g., headless CI or remote dev machine), SSH to a machine that has them:
```bash
scp /tmp/diagram.png user@laptop:/tmp/diagram.png
ssh laptop "gh-attach --repo owner/repo --md /tmp/diagram.png"
```

## Element format reference

### Required fields (all elements)

`type`, `id` (unique string), `x`, `y`, `width`, `height`

### Defaults (skip these)

- `strokeColor`: `"#1e1e1e"`
- `backgroundColor`: `"transparent"`
- `fillStyle`: `"solid"`
- `strokeWidth`: `2`
- `roughness`: `1` (hand-drawn look)
- `opacity`: `100`

### Element types

**Rectangle**:
```json
{ "type": "rectangle", "id": "r1", "x": 100, "y": 100, "width": 200, "height": 100 }
```
- `roundness: { "type": 3 }` for rounded corners
- `backgroundColor: "#a5d8ff"`, `fillStyle: "solid"` for filled

**Ellipse**:
```json
{ "type": "ellipse", "id": "e1", "x": 100, "y": 100, "width": 150, "height": 150 }
```

**Diamond**:
```json
{ "type": "diamond", "id": "d1", "x": 100, "y": 100, "width": 150, "height": 150 }
```

**Labeled shape (container binding)** -- create a text element bound to the shape:

> **WARNING:** Do NOT use `"label": { "text": "..." }` on shapes. This is NOT a valid
> Excalidraw property and will be silently ignored, producing blank shapes. You MUST
> use the container binding approach below.

The shape needs `boundElements` listing the text, and the text needs `containerId` pointing back:

```json
{ "type": "rectangle", "id": "r1", "x": 100, "y": 100, "width": 200, "height": 80,
  "roundness": { "type": 3 }, "backgroundColor": "#a5d8ff", "fillStyle": "solid",
  "boundElements": [{ "id": "t_r1", "type": "text" }] },
{ "type": "text", "id": "t_r1", "x": 105, "y": 110, "width": 190, "height": 25,
  "text": "Hello", "fontSize": 20, "fontFamily": 1, "strokeColor": "#1e1e1e",
  "textAlign": "center", "verticalAlign": "middle",
  "containerId": "r1", "originalText": "Hello", "autoResize": true }
```

- Works on rectangle, ellipse, diamond
- Text is auto-centered by Excalidraw when `containerId` is set
- `originalText` should match `text`
- Always include `fontFamily: 1` (Virgil/hand-drawn font)

**Labeled arrow** -- same container binding approach:

```json
{ "type": "arrow", "id": "a1", "x": 300, "y": 150, "width": 200, "height": 0,
  "points": [[0,0],[200,0]], "endArrowhead": "arrow",
  "boundElements": [{ "id": "t_a1", "type": "text" }] },
{ "type": "text", "id": "t_a1", "x": 370, "y": 130, "width": 60, "height": 20,
  "text": "connects", "fontSize": 16, "fontFamily": 1, "strokeColor": "#1e1e1e",
  "textAlign": "center", "verticalAlign": "middle",
  "containerId": "a1", "originalText": "connects", "autoResize": true }
```

**Standalone text** (titles and annotations only):

```json
{ "type": "text", "id": "t1", "x": 150, "y": 138, "text": "Hello", "fontSize": 20,
  "fontFamily": 1, "strokeColor": "#1e1e1e", "originalText": "Hello", "autoResize": true }
```

**Arrow**:

```json
{ "type": "arrow", "id": "a1", "x": 300, "y": 150, "width": 200, "height": 0,
  "points": [[0,0],[200,0]], "endArrowhead": "arrow" }
```

- `points`: `[dx, dy]` offsets from element `x`, `y`
- `endArrowhead`: `null` | `"arrow"` | `"bar"` | `"dot"` | `"triangle"`
- `strokeStyle`: `"solid"` (default) | `"dashed"` | `"dotted"`

### Arrow bindings (connect arrows to shapes)

```json
{
  "type": "arrow", "id": "a1", "x": 300, "y": 150, "width": 150, "height": 0,
  "points": [[0,0],[150,0]], "endArrowhead": "arrow",
  "startBinding": { "elementId": "r1", "fixedPoint": [1, 0.5] },
  "endBinding": { "elementId": "r2", "fixedPoint": [0, 0.5] }
}
```

`fixedPoint` coordinates: `top=[0.5,0]`, `bottom=[0.5,1]`, `left=[0,0.5]`, `right=[1,0.5]`

### Drawing order (z-order)

- Array order = z-order (first = back, last = front)
- Emit progressively: background zones -> shape -> its bound text -> its arrows -> next shape
- Always place the bound text element immediately after its container shape

### Sizing guidelines

**Font sizes:**
- Minimum `fontSize`: **16** for body text, labels
- Minimum `fontSize`: **20** for titles and headings
- Minimum `fontSize`: **14** for secondary annotations only (sparingly)
- NEVER use `fontSize` below 14

**Element sizes:**
- Minimum shape size: 120x60 for labeled rectangles/ellipses
- Leave 20-30px gaps between elements minimum

### Color palette

See `references/colors.md` for full tables. Quick reference:

| Use | Fill Color | Hex |
|-----|-----------|-----|
| Primary / Input | Light Blue | `#a5d8ff` |
| Success / Output | Light Green | `#b2f2bb` |
| Warning / External | Light Orange | `#ffd8a8` |
| Processing / Special | Light Purple | `#d0bfff` |
| Error / Critical | Light Red | `#ffc9c9` |
| Notes / Decisions | Light Yellow | `#fff3bf` |
| Storage / Data | Light Teal | `#c3fae8` |

### Tips

- Use the color palette consistently across the diagram
- **Text contrast is CRITICAL** -- never use light gray on white. Minimum text color on white: `#757575`
- Do NOT use emoji in text -- they don't render in Excalidraw's font
- For dark mode diagrams, see `references/dark-mode.md`
- For larger examples, see `references/examples.md`
