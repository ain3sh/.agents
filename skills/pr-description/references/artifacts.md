# PR artifact publication

`show-me` owns explanatory diagrams and code views, including format, render
checks, and theme-aware embedding. `references/visual-evidence.md` owns live
proof of a visual change. This file owns their PR upload and placement.

## Upload

Upload only as part of an authorized PR publish/update request. **Use
`gh-attach`** for GitHub user attachments; never commit images/videos to a PR
branch or use `raw.githubusercontent.com`. Exclude secrets, tokens, and
machine-specific paths from the artifact and its caption.

```bash
gh-attach --repo owner/repo --url /absolute/path/diagram.png
```

By default it uses `GH_TOKEN`; `--user <account>` uses that logged-in gh
account's token instead, which may carry scopes `GH_TOKEN` lacks (uploads need
`repo`, and a scopeless token gets 404).

Delegated and cloud sessions hold a GitHub App token, which the upload
endpoint rejects (404 or `unsupported authentication type`); the cookie
fallback `gh-attach` suggests is a dead end there. Push the files under
`.attachments/` on an `attachments/<repo>/<slug>` branch instead; the repo's
workflow uploads them and logs the URLs (factory-mono:
`.github/workflows/upload-attachments.yml`, recipe in its `AGENTS.md`,
"Screenshots and videos").

Each view is one opaque PNG ([show-me Image](../../show-me/references/surfaces.md#image));
embed it as `<img alt="<takeaway>" src="<url>" />` with alt text that states
its takeaway, not its topic. Locally without a browser-authenticated GitHub
session, use `--session-file`; don't expose session material. Keep
machine/auth details out of public PR prose.

## Placement

- Explanatory views go under `## Architecture` as uploaded images; only
  verbatim source the reader copies stays Markdown text. Return to
  `references/publish.md` for the body write.
- The demo video goes in **What**; live screenshots and other recordings go
  under `## Visual Evidence`, per `references/visual-evidence.md`.
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
