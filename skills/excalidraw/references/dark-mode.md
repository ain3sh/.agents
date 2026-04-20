# Excalidraw Dark Mode Diagrams

Dark mode is produced by two things working together. Use both, nothing more:

1. `appState.viewBackgroundColor: "#1e1e2e"` -- the canvas colour when the raw `.excalidraw` file is opened in excalidraw.com.
2. `excalirender --dark -s 2` -- applies Excalidraw's dark theme at render time.

**Do NOT add a full-canvas background rectangle** (e.g. a `10000x7500` filled rect as element 0). Excalirender renders the full scene bounding box, so such a rect turns a tight 400x200 diagram into a `20000x15000` PNG where the real content is a few-pixel speck, and `--dark` inverts the rect's dark fill to pale gray. `viewBackgroundColor` + `--dark` already deliver a dark canvas without either side-effect.

Envelope for every dark-mode diagram:

```json
{
  "type": "excalidraw",
  "version": 2,
  "source": "droid",
  "elements": [ ...your elements, no background rect... ],
  "appState": { "viewBackgroundColor": "#1e1e2e" }
}
```

## Text Colors (on dark)

| Color | Hex | Use |
|-------|-----|-----|
| White | `#e5e5e5` | Primary text, titles |
| Muted | `#a0a0a0` | Secondary text, annotations |
| NEVER | `#555` or darker | Invisible on dark bg |

## Shape Fills (on dark)

| Color | Hex | Good For |
|-------|-----|----------|
| Dark Blue | `#1e3a5f` | Primary nodes |
| Dark Green | `#1a4d2e` | Success, output |
| Dark Purple | `#2d1b69` | Processing, special |
| Dark Orange | `#5c3d1a` | Warning, pending |
| Dark Red | `#5c1a1a` | Error, critical |
| Dark Teal | `#1a4d4d` | Storage, data |

## Stroke and Arrow Colors (on dark)

Use the standard Primary Colors -- they're bright enough on dark backgrounds:
Blue `#4a9eed`, Amber `#f59e0b`, Green `#22c55e`, Red `#ef4444`, Purple `#8b5cf6`

For subtle shape borders, use `#555555`.

## Example: Dark mode labeled rectangle

```json
[
  {
    "type": "rectangle", "id": "r1",
    "x": 100, "y": 100, "width": 200, "height": 80,
    "backgroundColor": "#1e3a5f", "fillStyle": "solid",
    "strokeColor": "#4a9eed", "strokeWidth": 2,
    "roundness": { "type": 3 },
    "boundElements": [{ "id": "t_r1", "type": "text" }]
  },
  {
    "type": "text", "id": "t_r1",
    "x": 105, "y": 120, "width": 190, "height": 25,
    "text": "Dark Node", "fontSize": 20, "fontFamily": 1,
    "strokeColor": "#e5e5e5",
    "textAlign": "center", "verticalAlign": "middle",
    "containerId": "r1", "originalText": "Dark Node", "autoResize": true
  }
]
```

Always set `"strokeColor": "#e5e5e5"` on standalone text elements on dark backgrounds. The default `#1e1e1e` is invisible.
