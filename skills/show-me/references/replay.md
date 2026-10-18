# Behavioral replay

Run after editing this skill, or when a caller reports weak output. Each
scenario is a real prompt against real code; grade the produced view, not the
skill's wording. A scenario passes only when every grading row holds.

## Scenarios

| # | Prompt | Destination | Expected output |
|---|---|---|---|
| 1 | "Explain the architecture of this PR" on a multi-concern diff (3+ unrelated concerns, 15+ files) with no dominant relationship | GitHub body | One useful relation per named concern the reviewer must hold (call tree, types, or sequence with symbols from the diff); a PR body never omits the section. Never a `diff` or tree whose branches enumerate concerns. |
| 2 | `/show-me how <function> picks <thing>` on an actual algorithm | Terminal | Typed code or labelled pseudocode showing branches, mutations, and return; verbatim lines carry their path; no Mermaid fence; no prose transcription after it. |
| 3 | `/show-me <simple fact>` (which module exports X, which flag gates Y) | Terminal | One sentence, no view. |
| 4 | `/show-me <request flow> as sequence` across four actors, answered once in the terminal and once for a PR comment | Terminal, then GitHub | Numbered actor-message lines in the terminal; `sequenceDiagram` with payloads on arrows for GitHub; same actors and messages in both. |
| 5 | `/show-me <component> tree as html` | Browser | One self-contained file at the requested path or a unique `/tmp/YYYY-MM-DD-show-me-*.html`; no CDN; legible at about 400px and 1200px in light and dark with no horizontal page or diagram scrolling; code is selectable text; the reply gives the local link, a one-line caption, optionally a preview; nothing uploaded. |
| 6 | Scenario 5's file requested inside a PR body | GitHub body | HTML is not pasted into the body; any rendering goes through `pr-description/references/artifacts.md` in that workflow's publish step; code stays Markdown in the body; nothing is uploaded from a bare `/show-me`. |
| 7 | "Reuse this PR diagram in the design doc" with local Excalidraw source, a gated attachment URL, and an existing themed template | Browser document | Reuse the verified drawing as SVG, with theme variants if needed; no base64 PNG or auth-gated hotlink. Preserve selectable code and the caller's components. The document workflow retains full-page verification and its gist truncation check. No publication unless requested. |
| 8 | "Show the component ownership and then the failure timeline" with evidence supporting both questions | PR or document | Two complementary views, each answering its own question, not a forced single mega-diagram or duplicate illustrations. Both use the same verified actors. |
| 9 | "/show-me how the triggers change, Slack-friendly" in a Slack thread, on a before/after across 4+ triggers | Slack | Before/after panels rendered from one HTML file to an opaque 2× PNG, checked with a high-quality `Read`; delivered through `slack-cli` only when the reply is authorized. The text reply answers the question first and does not restate the image. No ASCII panels or Markdown table in a code block. |
| 10 | Review verdict for a PR that patches a symptom one layer below where the invariant lives | GitHub review body | One causal flow or call tree with real symbols marking where the invariant lives and the edge the PR patches; it carries the ruling instead of a prose trace, restates no line comment, and reads in both the approval-gate chat and GitHub. |
| 11 | PR body for a one-line config default change (or a README typo fix), view required | GitHub body | One small view placing the change on the path that reads it (key → reader call tree, or file → surface that renders it), with real symbols; no "nothing to draw", no one-sentence exit, no repeat of the hunk. |
| 12 | Review verdict `APPROVE` on a small right-layer fix whose body already has a verified Architecture view | GitHub review body | One view locating the change at the invariant's owner that adds what the body's view omits; it restates neither the body's view, a line comment, nor the hunk, and reads in both the gate chat and GitHub. |
## Grading

| Check | Pass |
|---|---|
| Recoverable | A reader who sees only the view reads off the relationship, order, or code shape it answers; every indentation, arrow, and row encodes a relation. |
| Faithful | Every symbol, file, edge, and quoted line resolves in the source at the cited revision; pseudocode, illustrative blocks, and elisions are labelled. |
| Surface-correct | Plain-terminal output contains no ```` ```mermaid ```` or HTML; GitHub output contains no styled or scripted HTML; Slack output contains no Markdown table, header, Mermaid, or ASCII panels. |
| Renders | Mermaid parses and its render is inspected; HTML and its core diagram reflow legibly at about 400px (code-only horizontal scroll allowed when syntax cannot wrap). A blocked renderer means an unverified draft, not a pass. |
| Source access | Reachable links resolve; blocked links are reported as unchecked. Downloaded image content decodes as an image, never a login/SAML HTML page. |
| Authorized | No upload, publish, or PR edit happened outside the owning workflow's publish step; a requested output path was honored, otherwise a unique file was written. |
| Budgeted | Nothing repeats the prose; no implication that transcribes the view; a simple fact got a sentence. |

Record failures as the scenario number plus the failed check and the offending
fragment, then fix the skill text that produced it rather than the output.
