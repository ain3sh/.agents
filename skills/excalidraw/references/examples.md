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

> **IMPORTANT:** Text labels use container binding (`containerId` + `boundElements`); the `"label"` property is silently ignored. Each example's title declares its register; see SKILL.md Visual register for field values.

---

## Example 1: Two Connected Labeled Boxes (technical register)

```json
[
  { "type": "text", "id": "title", "x": 280, "y": 30, "text": "Simple Flow", "fontSize": 28, "fontFamily": 2, "originalText": "Simple Flow", "autoResize": true },
  { "type": "rectangle", "id": "b1", "x": 100, "y": 100, "width": 200, "height": 100, "roundness": { "type": 3 }, "backgroundColor": "#a5d8ff", "fillStyle": "solid", "roughness": 0, "boundElements": [{ "id": "t_b1", "type": "text" }, { "id": "a1", "type": "arrow" }] },
  { "type": "text", "id": "t_b1", "x": 105, "y": 130, "width": 190, "height": 25, "text": "Start", "fontSize": 20, "fontFamily": 2, "textAlign": "center", "verticalAlign": "middle", "containerId": "b1", "originalText": "Start", "autoResize": true },
  { "type": "rectangle", "id": "b2", "x": 450, "y": 100, "width": 200, "height": 100, "roundness": { "type": 3 }, "backgroundColor": "#b2f2bb", "fillStyle": "solid", "roughness": 0, "boundElements": [{ "id": "t_b2", "type": "text" }, { "id": "a1", "type": "arrow" }] },
  { "type": "text", "id": "t_b2", "x": 455, "y": 130, "width": 190, "height": 25, "text": "End", "fontSize": 20, "fontFamily": 2, "textAlign": "center", "verticalAlign": "middle", "containerId": "b2", "originalText": "End", "autoResize": true },
  { "type": "arrow", "id": "a1", "x": 300, "y": 150, "width": 150, "height": 0, "points": [[0,0],[150,0]], "endArrowhead": "arrow", "roughness": 0, "startBinding": { "elementId": "b1", "fixedPoint": [1, 0.5] }, "endBinding": { "elementId": "b2", "fixedPoint": [0, 0.5] } }
]
```

---

## Example 2: Sequence Diagram, UML-style (technical register)

```json
[
  {"type":"text","id":"title","x":200,"y":15,"text":"Sequence Flow","fontSize":24,"fontFamily":2,"originalText":"Sequence Flow","autoResize":true},

  {"type":"rectangle","id":"uHead","x":60,"y":60,"width":100,"height":40,"backgroundColor":"#a5d8ff","fillStyle":"solid","roundness":{"type":3},"strokeColor":"#4a9eed","roughness":0,"boundElements":[{"id":"t_uHead","type":"text"}]},
  {"type":"text","id":"t_uHead","x":65,"y":65,"width":90,"height":20,"text":"Client","fontSize":16,"fontFamily":2,"textAlign":"center","verticalAlign":"middle","containerId":"uHead","originalText":"Client","autoResize":true},
  {"type":"arrow","id":"uLine","x":110,"y":100,"width":0,"height":400,"points":[[0,0],[0,400]],"strokeColor":"#b0b0b0","strokeWidth":1,"strokeStyle":"dashed","roughness":0,"endArrowhead":null},

  {"type":"rectangle","id":"aHead","x":230,"y":60,"width":100,"height":40,"backgroundColor":"#d0bfff","fillStyle":"solid","roundness":{"type":3},"strokeColor":"#8b5cf6","roughness":0,"boundElements":[{"id":"t_aHead","type":"text"}]},
  {"type":"text","id":"t_aHead","x":235,"y":65,"width":90,"height":20,"text":"Server","fontSize":16,"fontFamily":2,"textAlign":"center","verticalAlign":"middle","containerId":"aHead","originalText":"Server","autoResize":true},
  {"type":"arrow","id":"aLine","x":280,"y":100,"width":0,"height":400,"points":[[0,0],[0,400]],"strokeColor":"#b0b0b0","strokeWidth":1,"strokeStyle":"dashed","roughness":0,"endArrowhead":null},

  {"type":"rectangle","id":"sHead","x":420,"y":60,"width":130,"height":40,"backgroundColor":"#ffd8a8","fillStyle":"solid","roundness":{"type":3},"strokeColor":"#f59e0b","roughness":0,"boundElements":[{"id":"t_sHead","type":"text"}]},
  {"type":"text","id":"t_sHead","x":425,"y":65,"width":120,"height":20,"text":"Database","fontSize":16,"fontFamily":2,"textAlign":"center","verticalAlign":"middle","containerId":"sHead","originalText":"Database","autoResize":true},
  {"type":"arrow","id":"sLine","x":485,"y":100,"width":0,"height":400,"points":[[0,0],[0,400]],"strokeColor":"#b0b0b0","strokeWidth":1,"strokeStyle":"dashed","roughness":0,"endArrowhead":null},

  {"type":"arrow","id":"m1","x":110,"y":150,"width":170,"height":0,"points":[[0,0],[170,0]],"roughness":0,"endArrowhead":"arrow","boundElements":[{"id":"t_m1","type":"text"}]},
  {"type":"text","id":"t_m1","x":165,"y":130,"width":60,"height":20,"text":"request","fontSize":14,"fontFamily":2,"textAlign":"center","verticalAlign":"middle","containerId":"m1","originalText":"request","autoResize":true},

  {"type":"arrow","id":"m2","x":280,"y":200,"width":205,"height":0,"points":[[0,0],[205,0]],"strokeColor":"#8b5cf6","roughness":0,"endArrowhead":"arrow","boundElements":[{"id":"t_m2","type":"text"}]},
  {"type":"text","id":"t_m2","x":352,"y":180,"width":60,"height":20,"text":"query","fontSize":14,"fontFamily":2,"textAlign":"center","verticalAlign":"middle","containerId":"m2","originalText":"query","autoResize":true},

  {"type":"arrow","id":"m3","x":485,"y":260,"width":-205,"height":0,"points":[[0,0],[-205,0]],"strokeColor":"#f59e0b","roughness":0,"endArrowhead":"arrow","strokeStyle":"dashed","boundElements":[{"id":"t_m3","type":"text"}]},
  {"type":"text","id":"t_m3","x":352,"y":240,"width":60,"height":20,"text":"rows","fontSize":14,"fontFamily":2,"textAlign":"center","verticalAlign":"middle","containerId":"m3","originalText":"rows","autoResize":true},

  {"type":"arrow","id":"m4","x":280,"y":320,"width":-170,"height":0,"points":[[0,0],[-170,0]],"strokeColor":"#8b5cf6","roughness":0,"endArrowhead":"arrow","strokeStyle":"dashed","boundElements":[{"id":"t_m4","type":"text"}]},
  {"type":"text","id":"t_m4","x":165,"y":300,"width":60,"height":20,"text":"response","fontSize":14,"fontFamily":2,"textAlign":"center","verticalAlign":"middle","containerId":"m4","originalText":"response","autoResize":true}
]
```

---

## Example 3: Concept Map (conceptual register)

```json
[
  {"type":"text","id":"title","x":260,"y":20,"text":"Onboarding brainstorm","fontSize":28,"fontFamily":1,"originalText":"Onboarding brainstorm","autoResize":true},

  {"type":"ellipse","id":"center","x":300,"y":160,"width":200,"height":120,"roundness":{"type":3},"backgroundColor":"#fff3bf","fillStyle":"solid","roughness":1,"strokeWidth":1.5,"boundElements":[{"id":"t_center","type":"text"},{"id":"e1","type":"arrow"},{"id":"e2","type":"arrow"},{"id":"e3","type":"arrow"}]},
  {"type":"text","id":"t_center","x":305,"y":205,"width":190,"height":30,"text":"New user","fontSize":22,"fontFamily":1,"textAlign":"center","verticalAlign":"middle","containerId":"center","originalText":"New user","autoResize":false},

  {"type":"rectangle","id":"n1","x":60,"y":100,"width":180,"height":80,"roundness":{"type":3},"backgroundColor":"#a5d8ff","fillStyle":"solid","roughness":1,"strokeWidth":1.5,"boundElements":[{"id":"t_n1","type":"text"},{"id":"e1","type":"arrow"}]},
  {"type":"text","id":"t_n1","x":65,"y":125,"width":170,"height":30,"text":"Magic link","fontSize":18,"fontFamily":1,"textAlign":"center","verticalAlign":"middle","containerId":"n1","originalText":"Magic link","autoResize":false},

  {"type":"rectangle","id":"n2","x":560,"y":100,"width":180,"height":80,"roundness":{"type":3},"backgroundColor":"#b2f2bb","fillStyle":"solid","roughness":1,"strokeWidth":1.5,"boundElements":[{"id":"t_n2","type":"text"},{"id":"e2","type":"arrow"}]},
  {"type":"text","id":"t_n2","x":565,"y":125,"width":170,"height":30,"text":"First aha","fontSize":18,"fontFamily":1,"textAlign":"center","verticalAlign":"middle","containerId":"n2","originalText":"First aha","autoResize":false},

  {"type":"rectangle","id":"n3","x":310,"y":360,"width":180,"height":80,"roundness":{"type":3},"backgroundColor":"#d0bfff","fillStyle":"solid","roughness":1,"strokeWidth":1.5,"boundElements":[{"id":"t_n3","type":"text"},{"id":"e3","type":"arrow"}]},
  {"type":"text","id":"t_n3","x":315,"y":385,"width":170,"height":30,"text":"Nudge email","fontSize":18,"fontFamily":1,"textAlign":"center","verticalAlign":"middle","containerId":"n3","originalText":"Nudge email","autoResize":false},

  {"type":"arrow","id":"e1","x":240,"y":170,"width":60,"height":50,"points":[[0,0],[60,50]],"endArrowhead":"arrow","roughness":1,"strokeWidth":1.5,"startBinding":{"elementId":"n1","fixedPoint":[1,0.5]},"endBinding":{"elementId":"center","fixedPoint":[0,0.3]}},
  {"type":"arrow","id":"e2","x":500,"y":220,"width":60,"height":-50,"points":[[0,0],[60,-50]],"endArrowhead":"arrow","roughness":1,"strokeWidth":1.5,"startBinding":{"elementId":"center","fixedPoint":[1,0.3]},"endBinding":{"elementId":"n2","fixedPoint":[0,0.5]}},
  {"type":"arrow","id":"e3","x":400,"y":280,"width":0,"height":80,"points":[[0,0],[0,80]],"endArrowhead":"arrow","roughness":1,"strokeWidth":1.5,"startBinding":{"elementId":"center","fixedPoint":[0.5,1]},"endBinding":{"elementId":"n3","fixedPoint":[0.5,0]}}
]
```

---

## Notes

- **`"label"` is silently ignored** -- always use container binding; both shape and text must reference each other.
- **Set `fontFamily` and `roughness` explicitly** -- Excalidraw defaults (`1`/`1`) are conceptual; omitting them silently overrides the technical register. Don't mix registers within a file.
- **Text elements need `originalText` and `autoResize: true`.**
- **Check y-coordinates** -- elements overlap when values are too close.
- **Arrow labels need space** -- keep labels short or widen the arrow.
