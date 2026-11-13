# PR artifact publication

`show-me` owns explanatory diagrams and code views, including format, render
checks, and theme-aware embedding. `references/visual-evidence.md` owns live
proof of a visual change. This file owns their PR upload and placement.

## Upload

Upload only as part of an authorized PR publish/update request. Never commit
images/videos to a PR branch or use `raw.githubusercontent.com`. Exclude
secrets, tokens, and machine-specific paths from the artifact and its caption.

1. Upload with `gh-attach`:

   ```bash
   gh-attach --repo owner/repo --url /absolute/path/diagram.png
   ```

   It uploads with `GH_TOKEN`, and the upload needs a classic PAT (`ghp_`) or
   OAuth token (`gho_`) with `repo` scope: a scopeless token or a GitHub App
   token (`ghu_`, `ghs_`) gets 404. `--user <account>` uploads with a
   logged-in gh account's token instead, when `gh auth status` lists one.

2. If that fails, the route depends on where the PR is:
   - A Factory-AI repository: upload for that repository. An attachment
     uploaded for a private repository renders only there.
   - A public repository elsewhere: upload for `factory-plugins`. It is
     public, so its attachments render in any PR body, logged-out readers
     included, and anyone can open the file. Check that it shows nothing
     private first.
   - A private repository elsewhere: stop and ask the user to log in a gh
     account that can upload to it (for `--user`), or to send the uploaded
     URLs. An upload for a public repository would publish the file.

   Both uploads go through `upload-attachments.yml` in
   **Factory-AI/factory-mono**, which uploads with its own token for the
   Factory-AI repository `<repo>` named in the branch; nothing has to exist in
   the PR's repository. From a factory-mono checkout, run the recipe in its
   `AGENTS.md`, "Screenshots and videos": it pushes the files under
   `.attachments/` on an `attachments/<repo>/<slug>` branch and reads each URL
   from the workflow run's log. The recipe's note that an attachment renders
   only in the repository it was uploaded for applies to private repositories.

3. If that fails too, stop and report the failing command and its error. Never
   publish a text stand-in for a required image or a "could not attach" line.

Each view is one opaque PNG ([show-me Image](../../show-me/references/surfaces.md#image));
embed it, and every screenshot, as `<img alt="<takeaway>" src="<url>" />` with
alt text that states its takeaway, not its topic. Keep machine/auth details out
of public PR prose.

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
