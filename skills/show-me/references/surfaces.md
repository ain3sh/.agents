# Surfaces

The destination decides the grammar, never the view. Select the view first
(`representations.md`), then render it in what the destination displays.
Changing the renderer never fixes a badly chosen relationship.

| Destination | Displays | Grammar |
|---|---|---|
| Terminal (chat reply, CLI, tool output) | Markdown text and fenced code; a ```` ```mermaid ```` or HTML block appears as raw source unless the client is known to render it | typed fences, indented trees, aligned tables, numbered sequence lines |
| GitHub body or comment | Markdown, fenced code, Mermaid at the host's pinned version and theme, uploaded images; strips HTML styles and scripts | Mermaid for interaction, state, and graph; Markdown code for code shape; trees and hunks for structure |
| Browser file or document | HTML, inline SVG, embedded images, selectable code | one focused file, or a figure inside the caller's document |

This skill owns visual selection, construction, rendering, and embedding.
`excalidraw` supplies its authoring format and renderer commands; `design-doc`
supplies document components and tokens. Callers own placement and publication,
not a second diagram policy.

## Terminal

- Default to text grammars. Some chat clients render Mermaid or HTML, but the
  model cannot see which one is reading, so emit those only when the owning
  workflow states the client renders them.
- Keep lines under about 100 columns; the reader's pane is narrower than the
  model's output. Wrap tree labels rather than run wide.
- Sequences use numbered `actor → actor: message` lines.

## GitHub

- Mermaid supports direction (`LR`, `TB`), `subgraph` grouping, notes, edge
  labels, and theme directives, and it renders natively, is editable in the PR,
  and diffs as text. GitHub pins the Mermaid version and theme, so custom
  fonts, CSS, and `%%{init}%%` theming may be ignored, and layout control is
  less than a custom HTML view. Use real symbol or file names in nodes, data
  on edges, `<br/>` for long labels. Use HTML/SVG for custom responsive layout,
  or load `excalidraw` when an editable drawing is useful or already exists.
  Choose for readability, not only after Mermaid fails.
- Code: fenced with a language; path on the line above. Anything the reviewer
  should open gets a permalink pinned to a sha, never a branch:
  `https://github.com/<owner>/<repo>/blob/<sha>/<path>#L<n>-L<m>`.
- `diff` fences hold real source hunks or real structure lines, never summary
  bullets ("Layout must encode a relation" in `representations.md`).
- A browser HTML view does not embed. Capture the diagram, not the whole
  explanation page, as PNG at 2× display resolution. Keep its code companion
  as Markdown text so it stays selectable. Render light and dark variants for
  theme-aware destinations; use the picture pattern below. Return files to
  `pr-description/references/artifacts.md` for authorized upload and placement.
- Render check before delivery: parse the exact emitted Mermaid with the local
  `mermaid` package (never a retyped copy) and render it at PR reading width,
  then inspect that arrows land on the intended lifelines and labels do not
  collide. Reading the source is not rendering proof; Mermaid rejects
  characters that look harmless in prose. When rendering is delegated, hand
  over only after the passing result is back; when no renderer is reachable,
  deliver only a draft labelled `render unverified`.

## Browser

For `as html`, produce one focused file. For a document caller, return a figure
and optional code block using its existing CSS tokens and components, not a
second page scaffold or theme. In `design-doc`, these are `figure.diagram`,
the template's SVG classes, and `pre.code`; document-wide capture stays there.

Use HTML when the view benefits from custom layout: an annotated algorithm,
an ownership diagram beside a type definition, a sequence with more lanes than
Mermaid keeps legible. A standalone view is not a walkthrough (`/explain-diff`)
or an RFC (`design-doc`).

Recipe:

- File: the path the user requested; otherwise a unique name such as
  `/tmp/YYYY-MM-DD-show-me-<slug>-<HHMMSS>.html`, never overwriting another
  run. Write inside the workspace only when the harness requires it there.
  Self-contained: inline CSS, no CDN, no JS unless the view is interactive.
  Embedded figures inherit the caller's file location and asset policy.
- Semantic hierarchy: the heading names the question (`<h1>` only for a
  standalone file); one `<figure>` per view, `<figcaption>` for the implication,
  and `<pre><code>` for code. Give SVGs a title/accessible label and images alt text.
- Whitespace: one idea per viewport; at least 24px between blocks; prose at
  about 72ch, diagrams may run wider.
- Edges: short labelled arrows (SVG `<line>` plus `<text>`), one label each.
- Inline SVG inherits the document's themes through CSS variables/classes.
  Reuse its primary-path accent and neutral supporting colors; don't invent
  another palette. Size boxes to the rendered labels plus padding, not guessed
  character counts. Wait for fonts before checking text bounds and collisions.
- Code stays selectable text with syntax highlighting from `<span>` classes
  (keyword, type, string, comment) and a palette that follows
  `prefers-color-scheme`; never an image of code.
- Narrow viewport: at about 400px the page and the core diagram reflow (stack
  panels, wrap labels, switch a wide SVG to a vertical layout) and stay
  legible; never shrink an SVG into unreadable text or fall back to horizontal page
  scrolling. Only a code block may scroll horizontally, and only when its
  syntax cannot wrap.
- Verify the actual render at its delivery width, plus about 400px for
  responsive HTML, in light and dark (agent-browser or the caller's Playwright
  capture). Inspect arrow endpoints, label/box collisions, contrast, code
  clipping, and page overflow. Reuse passing captures of the unchanged view;
  don't repeat full-document or authenticated-UI checks for a local figure.

## Reusing and embedding assets

Reuse a verified existing diagram when it fits the destination. If its labels
would become unreadable, adapt the source layout or narrow the question;
reusing the drawing does not mean preserving an unsuitable aspect ratio.
Its format follows the destination:

- **HTML:** embed vector diagrams as SVG, not base64 PNG. Keep raster formats
  for intrinsically raster sources (screenshots/photos). A few large PNG data URIs
  can push a single-file document past its host's content limit.
- **Image-only destinations such as GitHub attachments:** render/capture PNG
  for display; keep editable/vector source separately. An editing link alone
  is not an inline diagram.
- **Excalidraw:** load that skill for JSON, register, and `excalirender` flags.
  For HTML, render transparent light/dark SVG variants; for image attachments,
  render PNG variants; that skill owns source-color and inversion rules.

Inline SVG can share document CSS. An SVG loaded through `<img>` cannot; embed
pre-rendered theme variants as `data:image/svg+xml;base64,...` instead. Use
this pattern for those data URIs or the uploaded PNG URLs:

```html
<picture>
  <source srcset="DARK_ASSET" media="(prefers-color-scheme: dark)">
  <img src="LIGHT_ASSET" alt="The relationship this diagram explains">
</picture>
```

For HTML documents, set `figure img, figure picture` to
`width: 100%; height: auto; display: block`. Inject encoded assets into
placeholder tokens with a small script instead of pasting large strings through
editor tools. The caller checks its host's size/truncation limit after publishing.

**Source access:** auth-gated GitHub attachments and private CDNs may work inside
their host but fail from `file://` or gist previews. Do not hotlink them there.
Use verified local image bytes for embedding; a successful HTTP response can
be a login/SAML HTML page, so check content type and decode the image before use.
Adding a GitHub token does not prove a session-gated attachment is downloadable.
For gated video, use a local poster linked to the asset's host page (the
`design-doc` template has `figure.demo`), or an authorized accessible media host.
Converting to GIF does not remove access restrictions on the resulting file.
Never move private material to a public host just to make an embed work.

Open source links you can reach; report auth-blocked links as unchecked. Local
Git blob/range checks establish source fidelity, not remote access. Report
unavailable render/access checks without escalating to account or GUI work
unless that verification is needed for the requested deliverable.

## Handover

Deliver the local path as a link, a one-line caption naming the relationship
the view shows, and optionally a captured preview when the harness displays
images. Do not restate the view as prose. Publishing or attaching belongs to
the owning workflow; never upload unrequested.
