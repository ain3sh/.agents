# Excalidraw Diagram Examples

Wrap each in the `.excalidraw` envelope before saving:

```json
{
  "type": "excalidraw",
  "version": 2,
  "source": "droid",
  "elements": [ ...elements from examples below... ],
  "appState": { "viewBackgroundColor": "#ffffff" }
}
```

> **IMPORTANT:** All text labels on shapes and arrows use container binding (`containerId` + `boundElements`).
> Do NOT use the non-existent `"label"` property.

---

## Example 1: Two Connected Labeled Boxes

```json
[
  { "type": "text", "id": "title", "x": 280, "y": 30, "text": "Simple Flow", "fontSize": 28, "fontFamily": 1, "strokeColor": "#1e1e1e", "originalText": "Simple Flow", "autoResize": true },
  { "type": "rectangle", "id": "b1", "x": 100, "y": 100, "width": 200, "height": 100, "roundness": { "type": 3 }, "backgroundColor": "#a5d8ff", "fillStyle": "solid", "boundElements": [{ "id": "t_b1", "type": "text" }, { "id": "a1", "type": "arrow" }] },
  { "type": "text", "id": "t_b1", "x": 105, "y": 130, "width": 190, "height": 25, "text": "Start", "fontSize": 20, "fontFamily": 1, "strokeColor": "#1e1e1e", "textAlign": "center", "verticalAlign": "middle", "containerId": "b1", "originalText": "Start", "autoResize": true },
  { "type": "rectangle", "id": "b2", "x": 450, "y": 100, "width": 200, "height": 100, "roundness": { "type": 3 }, "backgroundColor": "#b2f2bb", "fillStyle": "solid", "boundElements": [{ "id": "t_b2", "type": "text" }, { "id": "a1", "type": "arrow" }] },
  { "type": "text", "id": "t_b2", "x": 455, "y": 130, "width": 190, "height": 25, "text": "End", "fontSize": 20, "fontFamily": 1, "strokeColor": "#1e1e1e", "textAlign": "center", "verticalAlign": "middle", "containerId": "b2", "originalText": "End", "autoResize": true },
  { "type": "arrow", "id": "a1", "x": 300, "y": 150, "width": 150, "height": 0, "points": [[0,0],[150,0]], "endArrowhead": "arrow", "startBinding": { "elementId": "b1", "fixedPoint": [1, 0.5] }, "endBinding": { "elementId": "b2", "fixedPoint": [0, 0.5] } }
]
```

---

## Example 2: Sequence Diagram (UML-style)

```json
[
  {"type":"text","id":"title","x":200,"y":15,"text":"Sequence Flow","fontSize":24,"fontFamily":1,"strokeColor":"#1e1e1e","originalText":"Sequence Flow","autoResize":true},

  {"type":"rectangle","id":"uHead","x":60,"y":60,"width":100,"height":40,"backgroundColor":"#a5d8ff","fillStyle":"solid","roundness":{"type":3},"strokeColor":"#4a9eed","strokeWidth":2,"boundElements":[{"id":"t_uHead","type":"text"}]},
  {"type":"text","id":"t_uHead","x":65,"y":65,"width":90,"height":20,"text":"Client","fontSize":16,"fontFamily":1,"strokeColor":"#1e1e1e","textAlign":"center","verticalAlign":"middle","containerId":"uHead","originalText":"Client","autoResize":true},
  {"type":"arrow","id":"uLine","x":110,"y":100,"width":0,"height":400,"points":[[0,0],[0,400]],"strokeColor":"#b0b0b0","strokeWidth":1,"strokeStyle":"dashed","endArrowhead":null},

  {"type":"rectangle","id":"aHead","x":230,"y":60,"width":100,"height":40,"backgroundColor":"#d0bfff","fillStyle":"solid","roundness":{"type":3},"strokeColor":"#8b5cf6","strokeWidth":2,"boundElements":[{"id":"t_aHead","type":"text"}]},
  {"type":"text","id":"t_aHead","x":235,"y":65,"width":90,"height":20,"text":"Server","fontSize":16,"fontFamily":1,"strokeColor":"#1e1e1e","textAlign":"center","verticalAlign":"middle","containerId":"aHead","originalText":"Server","autoResize":true},
  {"type":"arrow","id":"aLine","x":280,"y":100,"width":0,"height":400,"points":[[0,0],[0,400]],"strokeColor":"#b0b0b0","strokeWidth":1,"strokeStyle":"dashed","endArrowhead":null},

  {"type":"rectangle","id":"sHead","x":420,"y":60,"width":130,"height":40,"backgroundColor":"#ffd8a8","fillStyle":"solid","roundness":{"type":3},"strokeColor":"#f59e0b","strokeWidth":2,"boundElements":[{"id":"t_sHead","type":"text"}]},
  {"type":"text","id":"t_sHead","x":425,"y":65,"width":120,"height":20,"text":"Database","fontSize":16,"fontFamily":1,"strokeColor":"#1e1e1e","textAlign":"center","verticalAlign":"middle","containerId":"sHead","originalText":"Database","autoResize":true},
  {"type":"arrow","id":"sLine","x":485,"y":100,"width":0,"height":400,"points":[[0,0],[0,400]],"strokeColor":"#b0b0b0","strokeWidth":1,"strokeStyle":"dashed","endArrowhead":null},

  {"type":"arrow","id":"m1","x":110,"y":150,"width":170,"height":0,"points":[[0,0],[170,0]],"strokeColor":"#1e1e1e","strokeWidth":2,"endArrowhead":"arrow","boundElements":[{"id":"t_m1","type":"text"}]},
  {"type":"text","id":"t_m1","x":165,"y":130,"width":60,"height":20,"text":"request","fontSize":14,"fontFamily":1,"strokeColor":"#1e1e1e","textAlign":"center","verticalAlign":"middle","containerId":"m1","originalText":"request","autoResize":true},

  {"type":"arrow","id":"m2","x":280,"y":200,"width":205,"height":0,"points":[[0,0],[205,0]],"strokeColor":"#8b5cf6","strokeWidth":2,"endArrowhead":"arrow","boundElements":[{"id":"t_m2","type":"text"}]},
  {"type":"text","id":"t_m2","x":352,"y":180,"width":60,"height":20,"text":"query","fontSize":14,"fontFamily":1,"strokeColor":"#1e1e1e","textAlign":"center","verticalAlign":"middle","containerId":"m2","originalText":"query","autoResize":true},

  {"type":"arrow","id":"m3","x":485,"y":260,"width":-205,"height":0,"points":[[0,0],[-205,0]],"strokeColor":"#f59e0b","strokeWidth":2,"endArrowhead":"arrow","strokeStyle":"dashed","boundElements":[{"id":"t_m3","type":"text"}]},
  {"type":"text","id":"t_m3","x":352,"y":240,"width":60,"height":20,"text":"rows","fontSize":14,"fontFamily":1,"strokeColor":"#1e1e1e","textAlign":"center","verticalAlign":"middle","containerId":"m3","originalText":"rows","autoResize":true},

  {"type":"arrow","id":"m4","x":280,"y":320,"width":-170,"height":0,"points":[[0,0],[-170,0]],"strokeColor":"#8b5cf6","strokeWidth":2,"endArrowhead":"arrow","strokeStyle":"dashed","boundElements":[{"id":"t_m4","type":"text"}]},
  {"type":"text","id":"t_m4","x":165,"y":300,"width":60,"height":20,"text":"response","fontSize":14,"fontFamily":1,"strokeColor":"#1e1e1e","textAlign":"center","verticalAlign":"middle","containerId":"m4","originalText":"response","autoResize":true}
]
```

---

## Common Mistakes

- **Do NOT use `"label"` property** -- silently ignored, producing blank shapes. Always use container binding.
- **Every bound text needs both sides linked** -- shape needs `boundElements` AND text needs `containerId`.
- **Include `originalText` and `autoResize: true`** on all text elements.
- **Include `fontFamily: 1`** on all text elements.
- **Check y-coordinates** -- elements overlap when values are close.
- **Arrow labels need space** -- keep labels short or make arrows wider.
- **Draw decorations LAST** -- they appear at the end of the array so they're on top.
