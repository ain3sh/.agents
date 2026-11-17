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
| 4 | `/show-me <request flow> as sequence` across four actors, answered once in the terminal and once for a PR comment | Terminal, then GitHub | Numbered actor-message lines in the terminal; an uploaded sequence image with payloads on arrows for GitHub, never a Mermaid fence; same actors and messages in both. |
| 5 | `/show-me <component> tree as html` | Browser | One self-contained file at the requested path or a unique `/tmp/YYYY-MM-DD-show-me-*.html`; no CDN; legible at about 400px and 1200px in light and dark with no horizontal page or diagram scrolling; code is selectable text; the reply gives the local link, a one-line caption, optionally a preview; nothing uploaded. |
| 6 | Scenario 5's file requested inside a PR body | GitHub body | HTML is not pasted into the body; any rendering goes through `pr-description/references/artifacts.md` in that workflow's publish step; verbatim source stays Markdown in the body; nothing is uploaded from a bare `/show-me`. |
| 7 | "Reuse this PR diagram in the design doc" with local Excalidraw source, a gated attachment URL, and an existing themed template | Browser document | Reuse the verified drawing as SVG, with theme variants if needed; no base64 PNG or auth-gated hotlink. Preserve selectable code and the caller's components. The document workflow retains full-page verification and its gist truncation check. No publication unless requested. |
| 8 | "Show the component ownership and then the failure timeline" with evidence supporting both questions | PR or document | Two complementary views, each answering its own question, not a forced single mega-diagram or duplicate illustrations. Both use the same verified actors. |
| 9 | "/show-me how the triggers change, Slack-friendly" in a Slack thread, on a before/after across 4+ triggers | Slack | Before/after panels rendered from one HTML file to an opaque 2× PNG, checked with a high-quality `Read`; delivered through `slack-cli` only when the reply is authorized. The text reply answers the question first and does not restate the image. No ASCII panels or Markdown table in a code block. |
| 10 | Review verdict for a PR that patches a symptom one layer below where the invariant lives | GitHub review body | One causal flow or call tree with real symbols marking where the invariant lives and the edge the PR patches; it carries the ruling instead of a prose trace, restates no line comment, and reads in both the approval-gate chat and GitHub. |
| 11 | PR body for a one-line config default change (or a README typo fix), view required | GitHub body | One small view placing the change on the path that reads it (key → reader call tree, or file → surface that renders it), with real symbols; no "nothing to draw", no one-sentence exit, no repeat of the hunk. |
| 12 | Review verdict `APPROVE` on a small right-layer fix whose body already has a verified Architecture view | GitHub review body | No view unless one carries a relation the ruling turns on that the body's view omits; never a redraw of the body's view, a line comment, or the hunk. A verdict with no view is complete. |
| 13 | "/show-me what this PR does to the session file" in a thread where a teammate asks whether rows are being removed, on a diff that changes what one persisted row holds | Slack | An artifact diff image built from a real sample captured on the base and on the change: untouched rows kept around the delta, row and byte totals in the header, cuts labelled. Never a call tree, a policy table, or the changed row alone. |
| 14 | "/show-me how the new value gets into that row" on scenario 13's diff | Terminal | A call tree or numbered sequence with real symbols from the diff, the changed edge marked. No artifact diff: the change alters stored data, but the question is about the code path. |
| 15 | "/show-me how many core lines this PR changes, broken down" in a Slack thread, on a PR whose diff stat counts a patch file, a move, or generated files | Slack | A breakdown image: the counting command and revision named, the rule for "core" stated, every level summing to its total row, the host's diff stat shown with the gap accounted for, the lowest rows named by file or symbol. Never the host's figure passed off as the core count, a churn total, or counts listed in prose. |
| 16 | "/show-me this PR" on scenario 15's PR | Terminal | The form its change earns (call tree, pseudocode, or diff of shape). No breakdown: nobody asked how big it is. |
| 17 | "/show-me where these failures come from and what fixes them" after a triage that counted failures by observed state, proved some mechanisms, left a remainder unexplained, and ruled others out | Slack | An attribution image: the count, source, and window in the title; observed-state, mechanism, and fix columns that each sum to the count; each mechanism's proof; an unresolved part with what keeps it open; unproven fix edges dashed; ruled-out mechanisms with the counts that ruled them out. Never a mechanism-only split, the remainder folded into a mechanism, or ruled-out causes dropped. |
| 18 | "/show-me why this request failed" on one failure with one path | Terminal | A causal flow marking the first wrong edge. No attribution: there is no counted set. |
| 19 | "/show-me where these errors come from and what fixes them" after thin triage notes: counts by transport, one mechanism confirmed for only part of its bucket, another seen in two repros with its match count unchecked, a part with no transport recorded, and a cause dismissed by a share of users rather than a count of events | Terminal | An attribution table that sums to the total: the confirmed part apart from the rest of its bucket, the repro-only mechanism with its count marked unknown, the untagged part its own row, and the dismissed cause left open because a share of users is not a count in the same population. Never a whole bucket drawn under the mechanism confirmed for part of it, or an estimated count. |

## Grading

| Check | Pass |
|---|---|
| Recoverable | A reader who sees only the view reads off the relationship, order, or code shape it answers; every indentation, arrow, and row encodes a relation. |
| Faithful | Every symbol, file, edge, and quoted line resolves in the source at the cited revision; pseudocode, illustrative blocks, and elisions are labelled. |
| Surface-correct | Plain-terminal output contains no ```` ```mermaid ```` or HTML; GitHub output contains no styled or scripted HTML, Mermaid fence, or ASCII panels; Slack output contains no Markdown table, header, Mermaid, or ASCII panels. |
| Renders | Every image is captured and inspected at high quality at its destination width; HTML and its core diagram reflow legibly at about 400px (code-only horizontal scroll allowed when syntax cannot wrap). A blocked renderer means an unverified draft, not a pass. |
| Source access | Reachable links resolve; blocked links are reported as unchecked. Downloaded image content decodes as an image, never a login/SAML HTML page. |
| Authorized | No upload, publish, or PR edit happened outside the owning workflow's publish step; a requested output path was honored, otherwise a unique file was written. |
| Budgeted | Nothing repeats the prose; no implication that transcribes the view; a simple fact got a sentence. |

Record failures as the scenario number plus the failed check and the offending
fragment, then fix the skill text that produced it rather than the output.

## Baseline

2026-11-16, scenario 17, Slack destination. Fixture: an untuned triage of 412
webhook "invalid signature" failures (four observed states, two proven
mechanisms, a 73-failure remainder, three ruled-out causes, four fixes), in
notes that list the facts out of order. Two blind workers read the skill by
path at neutral paths, without this file; one run per arm.

| Check | `main` (control) | Attribution edit |
|---|---|---|
| Count, source, window on top; every column sums to the count | Partial: count on top, window in the footer, no column sums | Pass: count and window in the header, `= 412` on every column |
| First column split on observed state | Partial: a state bar on top, but rows merge state into mechanism (41 + 32 become "unexplained") | Pass: a state column of its own, merged only into `unresolved` |
| Proof per mechanism; `unresolved` part with what keeps it open | Pass | Pass |
| Unproven fix coverage marked; diagnostic fix not drawn as a fix | Pass | Pass |
| Ruled-out mechanisms with their counts | Partial: counts in a one-line footnote | Pass: a section of its own, same population named |
| Slack reply answers first, does not restate the image | Pass | Pass |

The control already drew most of an attribution unprompted; the edit changed
the column structure (state, mechanism, fix, each summing to the count) and
promoted ruled-out causes to their own section. The fixture spells out proof
and ruled-out counts, so it cannot tell whether those rules matter when an
RCA's notes are thinner; scenario 19 below closes that. Both arms flagged the
same capture friction (viewport height), fixed in `surfaces.md`.

2026-11-16, round 2, terminal destination, one blind run per arm, same setup.

| Scenario | `main` (control) | Attribution edit |
|---|---|---|
| 18: one delivery, one path | Causal flow, first wrong edge marked | Causal flow, first wrong edge marked; no attribution |
| 19: thin triage notes | One causal flow per transport. All 640 stdio events sit under the OOM flow, with the 428 lacking an exit code mentioned only in prose; no column sums | Attribution table summing to 1,204: 212 OOM-confirmed apart from 428 unresolved, http's match count marked unknown, 154 untagged in their own row, the proxy left open because 3% of users is not a count of events |

Scenario 18 shows the edit does not pull a single failure into an attribution.
Scenario 19 is where the rules discriminate: without them, the control folded
428 unproven events under the confirmed mechanism. Neither arm quoted a skill
line as unclear.
