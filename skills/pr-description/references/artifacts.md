# PR artifact publication

`show-me` owns explanatory diagrams and code views, including format, render
checks, and theme-aware embedding. `references/visual-evidence.md` owns live
proof of a visual change. This file owns their PR upload and placement.

## Upload

Upload only as part of an authorized PR publish/update request. Never commit
images/videos to a PR branch or use `raw.githubusercontent.com`. Keep secrets,
tokens, and machine-specific paths out of the artifact, its caption, and the
PR prose.

1. Upload with `gh-attach`:

   ```bash
   gh-attach --repo owner/repo --url /absolute/path/diagram.png
   ```

   A 404 means the token cannot upload, not that `--repo` is wrong: GitHub
   rejects a GitHub App token (`ghu_`, `ghs_`) and any token without `repo`
   scope. Retry with `--user <account>` for each other account
   `gh auth status` lists.

2. If none can upload, use an upload workflow: CI that uploads the files you
   push with its own token and logs their URLs. It can live in any checkout,
   not only the PR's: `rg -l -g AGENTS.md user-attachments ~` finds its
   recipe. Upload for the PR's repository. If the workflow cannot and the
   PR's repository is public, upload for a public repository it can, after
   checking that the files show nothing private: a public repository's
   attachment opens for anyone, so it renders in any PR body.

3. Otherwise stop: report the failing command and its error, and ask the user
   to log in a gh account that can upload or to send the uploaded URLs. Never
   publish a text stand-in for a required image or a "could not attach" line.

Embed every image, a [show-me Image](../../show-me/references/surfaces.md#image)
view or a screenshot, as `<img alt="<takeaway>" src="<url>" />` with alt text
that states its takeaway, not its topic.

## Placement

- Explanatory views go under `## Architecture` as uploaded images; only
  verbatim source the reader copies stays Markdown text. Return to
  `references/publish.md` for the body write.
- The demo video and the artifact diff go in **What**; live screenshots and
  other recordings go under `## Visual Evidence`, per
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
