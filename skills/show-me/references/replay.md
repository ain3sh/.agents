# Behavioral replay

Run after editing this skill, or when a caller reports weak output. Each
scenario is a real prompt against real code; grade the produced view, not the
skill's wording. A scenario passes only when every grading row holds.

## Scenarios

| # | Prompt | Destination | Expected output |
|---|---|---|---|
| 1 | "Explain the architecture of this PR" on a multi-concern diff (3+ unrelated concerns, 15+ files) with no dominant relationship | GitHub body | One useful relation from a named concern (call tree, types, or sequence with symbols from the diff), or an explicit "no useful relation; omit the section". Never a `diff` or tree whose branches enumerate concerns. |
| 2 | `/show-me how <function> picks <thing>` on an actual algorithm | Terminal | Typed code or labelled pseudocode showing branches, mutations, and return; verbatim lines carry their path; no Mermaid fence; no prose transcription after it. |
| 3 | `/show-me <simple fact>` (which module exports X, which flag gates Y) | Terminal | One sentence, no view. |
| 4 | `/show-me <request flow> as sequence` across four actors, answered once in the terminal and once for a PR comment | Terminal, then GitHub | Numbered actor-message lines in the terminal; `sequenceDiagram` with payloads on arrows for GitHub; same actors and messages in both. |
| 5 | `/show-me <component> tree as html` | Browser | One self-contained file at the requested path or a unique `/tmp/YYYY-MM-DD-show-me-*.html`; no CDN; legible at about 400px and 1200px in light and dark with no horizontal page or diagram scrolling; code is selectable text; the reply gives the local link, a one-line caption, optionally a preview; nothing uploaded. |
| 6 | Scenario 5's file requested inside a PR body | GitHub body | HTML is not pasted into the body; any rendering goes through `pr-description/references/artifacts.md` in that workflow's publish step; code stays Markdown in the body; nothing is uploaded from a bare `/show-me`. |
| 7 | "Reuse this PR diagram in the design doc" with local Excalidraw source, a gated attachment URL, and an existing themed template | Browser document | Reuse the verified drawing as SVG, with theme variants if needed; no base64 PNG or auth-gated hotlink. Preserve selectable code and the caller's components. The document workflow retains full-page verification and its gist truncation check. No publication unless requested. |
| 8 | "Show the component ownership and then the failure timeline" with evidence supporting both questions | PR or document | Two complementary views, each answering its own question, not a forced single mega-diagram or duplicate illustrations. Both use the same verified actors. |

## Grading

| Check | Pass |
|---|---|
| Recoverable | A reader who sees only the view reads off the relationship, order, or code shape it answers; every indentation, arrow, and row encodes a relation. |
| Faithful | Every symbol, file, edge, and quoted line resolves in the source at the cited revision; pseudocode, illustrative blocks, and elisions are labelled. |
| Surface-correct | Plain-terminal output contains no ```` ```mermaid ```` or HTML; GitHub output contains no styled or scripted HTML. |
| Renders | Mermaid parses and its render is inspected; HTML and its core diagram reflow legibly at about 400px (code-only horizontal scroll allowed when syntax cannot wrap). A blocked renderer means an unverified draft, not a pass. |
| Source access | Reachable links resolve; blocked links are reported as unchecked. Downloaded image content decodes as an image, never a login/SAML HTML page. |
| Authorized | No upload, publish, or PR edit happened outside the owning workflow's publish step; a requested output path was honored, otherwise a unique file was written. |
| Budgeted | Nothing repeats the prose; no implication that transcribes the view; a simple fact got a sentence. |

Record failures as the scenario number plus the failed check and the offending
fragment, then fix the skill text that produced it rather than the output.
