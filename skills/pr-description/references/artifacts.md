# PR artifact publication

`show-me` owns explanatory diagrams and code views, including format, render
checks, and theme-aware embedding. `references/visual-evidence.md` owns live
proof of a visual change. This file owns their PR upload and placement.

## Upload

Upload only as part of an authorized PR publish/update request. **Use
`gh-attach`** for GitHub user attachments; never commit images/videos to the
repo or use `raw.githubusercontent.com`. Exclude secrets, tokens, and
machine-specific paths from the artifact and its caption.

```bash
gh-attach --repo owner/repo --url /absolute/path/diagram.png
```

For theme variants, upload each file and substitute its URL into the
[show-me picture pattern](../../show-me/references/surfaces.md#reusing-and-embedding-assets).
If the local machine lacks a browser-authenticated GitHub session, use a
trusted machine or `--session-file`; don't expose session material. Keep
machine/auth details out of public PR prose.

## Placement

- Explanatory views go under `## Architecture`, whether Mermaid, code, or an
  uploaded image. Return to `references/publish.md` for the body write.
- Live screenshots and recordings go under `## Visual Evidence`, per
  `references/visual-evidence.md`.
- Carry over show-me's caption and selectable code companion; don't add a
  prose transcription or a second rendering of the same view.
- An editable Excalidraw link is optional and needs authorization to upload
  the source to that host (`excalidraw` owns the command). Put it immediately
  below its image in `<details><summary>Edit diagram</summary>`, with the
  render command if useful. Don't make the editing link the primary
  deliverable: opening it can prompt readers to replace their current drawing.

## Screenshots & recordings

Caption live evidence with capture conditions (tool, dimensions, playback
speed), what to watch, and a measured delta where one exists (for example,
terminal-write bytes, request count, or p95 latency). Never invent a number
to fill the caption. A clip with no reading cue leaves the reviewer guessing.
