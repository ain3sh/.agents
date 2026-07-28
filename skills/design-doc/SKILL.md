---
name: design-doc
description: Author a publication-grade single-file HTML design doc or technical memo. Factory visual system, adaptive RFC/memo structure, fact-checked references, full light/dark Playwright verification, and secret-gist publishing.
---

A design doc here is one self-contained HTML file — fonts via Google Fonts, all styles inline, no JS framework — with the precision of an internal engineering artifact and the visual confidence of Factory product surfaces. The aesthetic exists to make reviewers actually read it; the structure exists to make the argument legible.

Output target: ~1.5k–3k lines, ~80–200 KB, prints to A4, dark-mode aware, publishable as a secret gist viewed via `gistpreview.github.io`.

## When to use

- Engineer asks for an RFC, design doc, ADR, monograph, technical spec, or sync-prep brief.
- Engineer needs an internal technical memo that sells a shipped capability with evidence rather than proposal boilerplate.
- A PR has architectural weight (≥2 reviewers, multiple sub-decisions) and needs framing beyond the PR description.
- A change touches a contract, persistence, or cross-component ownership and needs one shareable artifact.

**Skip this skill for** short READMEs, Linear ticket bodies, PR descriptions, slide decks, or anything best read in markdown — use markdown instead.

## Process recipe

The order matters. Skipping step 2 is the most common failure: prose ends up referencing constants or call sites that don't exist.

### 1. Frame the argument and choose the document mode

Choose the mode before touching HTML:

- **RFC / proposal:** problem → primer → goals/non-goals → proposal → decision cards → tradeoffs → rollout → open questions.
- **Technical memo / internal sell:** demand → structural constraint → evidence → shipped artifact → limits → deployment. Lead with a four-stat proof band and use charts/tables instead of decision-card boilerplate.
- **Sync prep:** decision needed → evidence → options → recommendation → unresolved questions.

Do not force the RFC scaffold onto a memo. A selling document should not read like a budget request, research diary, or next-cycle roadmap.

Name three things:
- **The single structural claim** — one sentence, ≤25 words. This becomes the tagline + §1 lede.
- **The 3–8 proof points or decisions** — decision cards in RFC mode; scorecards, comparisons, or deployment implications in memo mode.
- **The non-goals or current limits.** Keep them short and relevant to the chosen mode.

### 2. Source-of-truth pass

For every constant, file path, function signature, enum, and limit you intend to cite, run `rg` and verify. Write verified facts to a scratchpad. Two failure modes you will hit if you skip this:
- **Numeric limits.** Prior session caught `LOOP_MIN_INTERVAL_MS` referenced in prose — it didn't exist; the actual guard was `intervalMs < MINUTE_MS` inline.
- **Caps with multiple terms.** Prior session caught "jitter capped at 10%" that should have been "10% of period, capped at 15min."

When the PR description disagrees with the code, **the code wins** and you flag the discrepancy to the user.

### 3. Copy the template

```bash
cp ~/.agents/skills/design-doc/references/template.html <project>/.agents/specs/<slug>-design.html
```

Do not start from scratch. The styles encode hard-won decisions (Factory tokens, Geist hierarchy, `text-wrap: balance`, decision-card grid, auto-hide nav, dark/light modes, print stylesheet). The template is a working scaffold — render it once with the screenshot script in step 5 to confirm it loads before filling.

Before styling, search the repo for `DESIGN.md`, brand guidance, or live tokens. **The repo's design canon wins.** In Factory repos, read `packages/core-ui/src/DESIGN.md`; the bundled template follows that dark-first system.

### 4. Fill the scaffold top-down

For RFC mode, fill the scaffold top-down:

1. `<title>`, eyebrow, `h1.title`, `.tagline`, `.meta` strip. Keep only meta fields that earn their slot — a reviewer roster is fat unless the user asks for it.
2. **Optional** `figure.demo` if there's a demo video — see [Embedding video](#embedding-video).
3. §1 Summary — `.lede` with `.dropcap` + 1 supporting paragraph (zero-context rules below).
4. §2 Context — reader primer first, then what breaks today (tickets spelled out), why now.
5. §3 Goals & non-goals — `.two-col > .panel`.
6. §4 Proposal — `.pullquote` thesis + `figure.diagram` SVG + prose.
7. §5 Key decisions — `article.decision` × N. **Usually 60–70% of the doc by length.**
8. §6 Tradeoffs — `table.kv` or short prose.
9. §7 Rollout & verification — feature-flag posture, telemetry, rollback.
10. §8 Open questions — `ol.numbered`, **ordered by how much each answer would change the design** (highest leverage first).
11. `footer.doc` (provenance: PR, ticket, HEAD sha, file path). The template ships no colophon — typographic-credits sections read as flourish and get cut in review; don't add one unless asked.

Skip a section only if it's genuinely empty for this change — don't pad.

For memo mode, replace the goals/decision-card spine with the structure selected in step 1. Keep the same components and verification loop, but remove unused template furniture rather than leaving empty RFC sections.

**Write for a reader with zero context (review-tested — violating these draws "hard to read, context implicit and out of order" feedback):**

- **§1 Summary lede = 1–2 sentences a completely new reader understands**: the user-visible problem in plain words, then the fix in plain words. No internal vocabulary that only makes sense after §4 ("separate liveness from commit"-style taglines read as meaningless), and never open with a non-goal ("the visual shape is unchanged") — it buries the why.
- **§2 Context opens with a basics primer** before any deep-dive: define the system being changed and its load-bearing primitives, and define terms the rest of the doc leans on ("monotonic", "idempotent", …) — what they mean *here* and why they matter. Goals/Non-goals must read cleanly using only words the primer introduced.
- **Spell out every motivating ticket in-doc**: bold `ID — symptom` title, then 2–3 sentences of user-visible failure + mechanism. A bare tracker link is not context; the reader must never need to open Linear to follow the argument.
- **Order = how a stranger builds context**: problem → primer → mechanism of failure → concrete failures → goals → proposal. When revising a published doc against reviewer feedback, keep it a controlled change — touch only the sections the feedback targets.

### 5. Iteration loop (mandatory)

Write → capture → inspect → fix:

```bash
node ~/.agents/skills/design-doc/references/screenshot.js <abs-path-to-html>
# → /tmp/doc-previews/scroll-light-NN.png
#   /tmp/doc-previews/scroll-dark-NN.png
#   /tmp/doc-previews/hero-dark-v2.png
```

Playwright must resolve: run from a repo root whose `node_modules` ships it, or from anywhere with `NODE_PATH=<repo-root>/node_modules node …`. From a bare `/tmp` it dies with `ERR_MODULE_NOT_FOUND`. Use this reference script — don't recreate an ad-hoc capture script in `/tmp`; it won't survive the session.

The script clears stale captures with these filenames before rendering, then captures the full document in both color schemes. **Read every light and dark PNG with the `Read` tool at `image_quality="high"`.** A dark hero alone is insufficient: charts, tables, diagrams, and callouts often fail several viewports below it. Fix layout, contrast, and overflow bugs visually before tightening prose. Bugs you will only catch this way:
- `dl > dd` falling under `dt` instead of into column 2 → the template pins `grid-column: 2`; if you copied a card and removed it, restore it.
- Dark-mode contrast failures on `--code-bg` and `--accent-soft`.
- SVG text overflowing on narrow viewports.
- **TOC rail clipping**: the collapsed `nav.toc` must fit its widest roman numeral — at 56px "VIII" clipped to "VII"; the template now ships 68px. Recheck if you shrink the rail or exceed 8 sections.
- **SVG box captions touching or crossing rect edges**: in the template's 780-unit viewBox, `.cap` mono text runs ~6.5 units/char (titles wider). Size each `rect` to its longest caption plus ~30 units, or shorten the caption. Confirm with `image_quality="high"` reads — default quality hides near-edge overflow.

If layout is mysterious, run `inspect.js`:
```bash
node ~/.agents/skills/design-doc/references/inspect.js <abs-path> "<css-selector>"
```
It dumps bounding rects + computed styles for the first 12 matches.

### 6. Two content passes

After visual layout is clean:

- **Pass 1 — structural cuts.** If a fact appears in §1 and §5, delete it from §1 and link forward ("full list: D7"). The doc gets *shorter* in this pass, not longer. **Cut template furniture** — scaffolding prose users reliably nuke as fat:
  - Section meta-intros that describe the section instead of adding content ("Eight decisions carry this PR…", "The parts where good engineers could disagree…", "Each row is independently checkable."). The heading already does that work; open on the first real item.
  - Navigational cross-reference sentences in §1 ("§4 breaks the diff into…; §5 defends…; §7 records…") — the TOC is the map.
  - Audience lead-ins ("A primer for readers outside the SDK effort.") — just start the primer.
- **Pass 2 — polish.** Read aloud (literally, your inner voice catches bumps). Replace neologisms ("due-times" → "task that came due three times"), kill "actually", strip "we can", tighten cross-references. Each edit should remove or replace text, rarely add.
- **Pass 2.5: voice sweep.** Load **voice** for a quick craft pass focused on anti-slop, false agency, and filler. Keep edits surgical and preference-light so this reads as an independent quality gate, not a rewrite.

### 7. Re-verify

Re-run `screenshot.js`. **`scrollHeight` should drop, not grow.** Prior session went 18820 → 18429 px and 17 → 14 segments with no information lost.

### 8. Publish (optional)

See [Publishing](#publishing).

## Aesthetic foundation

The bundled default follows Factory's visual system:

- **Dark-first:** black canvas, white foreground, warm gray support text. Light mode exists for marketing/install surfaces and print.
- **One accent:** Factory orange (`#EE6018`) marks active paths, key numerics, section metadata, and the primary comparison. It is not ambient decoration.
- **Flat surfaces:** no shadows, glows, gradients, glass, or elevation theater. Depth comes from surface contrast, 1px borders, spacing, and type.
- **Mono-led:** Geist Mono carries labels, metadata, code, chart axes, and diagram text. Geist carries headings and prose.
- **Restrained geometry:** 4px default radius, 6px only for large containers, pills only for actual tags.
- **Technical confidence:** left-align interiors, use generous outer margins, and let scale rather than bold weight carry hierarchy.

If the repo defines a different canon, adapt the tokens and typography to it. Do not invent an independent theme merely because the artifact is standalone.

## Typography craft

| Role | Factory treatment | Note |
|---|---|---|
| `body` | Geist 400, 18px, `line-height: 1.62`, `letter-spacing: -0.01em` | Larger, calmer body copy works better than compact editorial serif text for broad-team docs. |
| `h1.title` | Geist 300, 52–82px, `line-height: 0.98`, tracking `-0.045em` | Light weight plus scale creates authority without a marketing-heavy display face. |
| `.tagline` | Geist 400, 19–23px, muted foreground | Keep upright. No italic in Factory product or document surfaces. |
| `section.block > h3` | Geist 300, 32–44px, tracking `-0.035em` | Use type scale, not orange or bold weight, for section hierarchy. |
| `.dropcap` | Geist Mono 400, orange | A technical accent, not a decorative swash. Remove it if it feels literary rather than useful. |
| `.pullquote p` | Geist 300, 24–30px, upright, orange left rule | Treat it as an engineering assertion, not a quotation ornament. |
| All mono | Geist Mono 400, uppercase labels at `0.08em` | Use `font-feature-settings: "zero"` for numeric disambiguation. |

Use `text-wrap: balance` on headings, taglines, pullquotes, figcaptions, and decision titles. Use existing tokens and `color-mix(in oklab, …)` only for tonal versions of the canonical palette.

## Quantitative proof and charts

Internal selling docs often succeed or fail on the chart:

- Put a **four-stat proof band** directly under the hero when four numbers carry the thesis. Values use orange; labels and explanations stay neutral.
- Scale bars to the meaningful range, not mechanically from zero. For ROC-AUC, a `0.5 → 1.0` axis exposes useful signal far better than `0 → 1.0`. State the truncated baseline in the axis and caption.
- Give the shipped/recommended row the sole orange bar and a subtle orange-tinted surface. Render incumbents, controls, and frontier references in gray.
- If benchmark frames differ, separate them into visibly distinct groups and state that they are not directly comparable. Never imply a head-to-head comparison with color or proximity alone.
- Put the delta beside the winning value (`+12.5 pts`), not in a detached prose paragraph.
- Use 1px grid lines or pseudo-elements for reference marks. Do not use gradients to fake chart structure.

## Components inventory

All defined in `references/template.html` — read it for any pattern you're unsure of.

| Selector | Purpose | When to use |
|---|---|---|
| `.eyebrow` | Mono uppercase kicker w/ rule | Above titles & figure labels |
| `h1.title` + `.tagline` | Hero | Once, in `header.doc` |
| `.meta .field` | Status/author/ticket/PR grid | Once, after tagline |
| `.statband` | Four quantitative proof points | Memo/internal-sell mode, directly below the hero |
| `figure.demo` | Video poster card | Optional, between header and §1 |
| `section.block > h2/h3` | Numbered eyebrow + display heading | Every section |
| `.lede` + `.dropcap` | First-paragraph treatment | First paragraph of §1 only |
| `.two-col > .panel` | Side-by-side lists | Goals/non-goals, pros/cons |
| `article.decision` | D-card: Decision / Rationale / Alternatives / Consequence | Every key decision — the load-bearing component. Reviewers skim titles, then dt/dd rows. **Bullets are not a substitute.** |
| `aside.pullquote` | Mental-model or thesis quote | 1 per ~1500 words; should literally state the thesis in ≤25 words |
| `figure.diagram` + inline `<svg>` | Architecture/sequence diagrams | When the picture is faster than prose |
| `pre.code` w/ `.k`/`.s`/`.t`/`.fn`/`.hl` spans | Syntax-highlighted snippets | When citing actual call sites |
| `.callout` (`.rose`) | Notes, warnings | Sparingly — every callout devalues the rest |
| `table.kv` | Tradeoff matrices, limits tables | Comparing N options |
| `ol.numbered` | Roman-numeralled list | Open questions |
| `footer.doc` | Provenance (PR · ticket · HEAD sha · file path) | Once, at end |

**Citing code.** Use `<code>name</code>` for function/component names inline. File paths get one explicit anchor at the point of citation: "(see `apps/cli/src/services/scheduled-tasks/loopSchedule.ts:42`)". Reviewers `rg` from names; they don't click.

## Publishing

For internal docs, **secret gist + gistpreview** is the only path that reliably works without org infra:

```bash
gh gist create <path>/<slug>-design.html --desc "<title>"   # add --public only if the user asks
# → https://gist.github.com/<user>/<gist-id>
```

Share: `https://gistpreview.github.io/?<gist-id>/<slug>-design.html` (filename suffix required for multi-file gists, harmless otherwise)

Update: `gh gist edit <gist-id> <path>/<slug>-design.html`

**Revising an already-published doc** — keep the same gist id and filename so the gistpreview link already shared in PRs/Slack stays valid:

```bash
# pull the live copy to revise against (strip tags to a text outline if you only need structure)
gh api gists/<gist-id> --jq '.files["<slug>-design.html"].content' > current.html
# push: content is too large for -f flags; build {"description": ..., "files": {"<name>": {"content": ...}}}
# with a short python script, then
gh api gists/<gist-id> -X PATCH --input /tmp/gist-patch.json
```

The API path also updates the gist description. **Keep the file under ~1 MB.** The gist *contents* API truncates files past roughly that size: `GET gists/<id>` returns only the first ~1 MB and sets `"truncated": true`, and gistpreview renders through that API — so an oversized doc renders only partway through (the tail sections and footer silently vanish) even though the PATCH succeeded and the source is intact. A PATCH that bloats the file past the limit therefore *breaks* the preview without any error. After any PATCH, verify: `gh api gists/<id> --jq '.files["<name>"].truncated'` must be `false`. Almost always the bloat is inlined base64 images — see [Embedding diagrams (raster)](#embedding-diagrams-raster) for the SVG-not-PNG fix.

### Publishing dead ends (verified failures)

| Endpoint | Status |
|---|---|
| `gistcdn.githack.com/...`, `raw.githack.com/...` | **403 for secret gists** — public only |
| `htmlpreview.github.io/?<raw-url>` | Works for public gists, slow first-load, occasionally CSP-blocks Google Fonts |
| Direct gist raw URL | Served as `text/plain` — browser shows source, not rendered HTML |
| GitHub Pages on a private repo | Requires GitHub Enterprise |

If the doc must be public-link-shareable AND render reliably: make the gist public and use `gistcdn.githack.com`. **Confirm with the user first** — public gists list under their GH profile.

## Embedding video

GitHub `user-attachments/assets/...` URLs are **session-gated**: they only resolve to a streamable file when loaded inside `github.com` with a logged-in session. They will **not** play as `<video src>` from `file://` or from a gist. Trying to fetch them with `curl` + `gh auth token` returns an HTML stub, not the asset binary.

The template ships a poster-card pattern (`figure.demo`) that opens the asset in a new tab where the user's GitHub session resolves it. Use that. For embeddable playback, host the file on a CDN (S3, Cloudflare R2) or convert to GIF — or accept the poster card.

## Embedding diagrams (raster)

Default to the template's inline-`<svg>` `figure.diagram` — it inherits both themes via CSS classes. When a polished excalidraw diagram already exists (e.g., built for the PR), embed its renders instead of redrawing, but never hotlink: GitHub `user-attachments` image URLs are session-gated like video and 404 from gistpreview. Inline as base64 `data:` URIs:

⚠️ **Render diagrams to SVG, not PNG.** excalirender emits SVG (`-o name.svg`), and excalidraw vector diagrams are an order of magnitude smaller as SVG than as base64 PNG — typically ~20–40 KB vs ~300–500 KB *each*. Four base64 PNGs at `-s 2` blew one doc past 2 MB, which the gist API truncated and gistpreview rendered only halfway (the SVG re-do landed the same doc at ~290 KB). Reach for PNG only when the source is itself raster (a real screenshot/photo); for excalidraw/vector content, SVG is mandatory.

1. Render two transparent theme variants so the diagram inherits the doc's paper/dark background:
   `excalirender d.excalidraw -o light.svg --transparent -s 2` and `… -o dark.svg --transparent --dark -s 2`.
2. Inside `figure.diagram`, swap themes with `<picture>` and base64-`data:image/svg+xml` URIs:
   `<picture><source srcset="data:image/svg+xml;base64,DARK" media="(prefers-color-scheme: dark)"><img src="data:image/svg+xml;base64,LIGHT" alt="…"></picture>` + a `<figcaption>`.
3. Add `figure.diagram img, figure.diagram picture { width: 100%; height: auto; display: block; }` beside the existing `svg` rule.
4. Author the HTML with placeholder tokens and inject the base64 with a small python pass — don't paste large strings through editor tools.
5. After publishing, confirm the gist is not truncated (see [Publishing](#publishing)) and verify both themes with the screenshot loop.

## Verification checklist

Before declaring done:

**Facts**
- [ ] Every cited constant / file path / function signature was verified with `rg` against source.
- [ ] PR description and code agree on numerics; if not, code wins and the discrepancy is flagged.

**Reader**
- [ ] §1 lede passes the zero-context test (plain-words problem + fix, no internal jargon, no leading non-goal).
- [ ] §2 opens with the primer; every motivating ticket is described in-doc — the reader never needs to open the tracker.

**Structure**
- [ ] The document follows the mode chosen in step 1; memo mode contains no empty RFC sections or vestigial decision cards.
- [ ] In RFC mode, each `article.decision` has all four `dt` slots: Decision, Rationale, Alternatives rejected, Consequence.
- [ ] Open questions, when present, are ordered by leverage (highest first).
- [ ] No literal "TODO" or `<!-- TODO -->` markers remain.
- [ ] No template furniture: colophon, reviewer roster, section meta-intros, and §1 cross-ref sentences are absent unless the user asked for them.

**Visual**
- [ ] Every light and dark Playwright segment was inspected; no contrast failures on charts, tables, diagrams, code blocks, or accent surfaces.
- [ ] Print stylesheet renders without overflow (Chrome → Cmd-P → check pagination).
- [ ] `scrollHeight` after Pass 2 is ≤ `scrollHeight` after Pass 1. If it grew, you bloated.
- [ ] Factory mode uses no italics, gradients, shadows, glass, or decorative second accent.
- [ ] Orange identifies the primary path or proof point; controls and reference rows remain neutral.

**Publish**
- [ ] After any gist create/PATCH, `gh api gists/<id> --jq '.files["<name>"].truncated'` is `false` (file under ~1 MB), and the live gistpreview renders through the footer — not just the first sections. Diagrams are SVG, not base64 PNG.

## Dead ends (warnings)

- ⚠️ **Don't inspect only the dark hero.** The full dark scroll catches failures in lower charts, tables, diagrams, and callouts that the first viewport cannot.
- ⚠️ **Don't use orange as ambient decoration.** If every border, heading, and comparison row is orange, nothing is primary. Keep controls and secondary comparisons gray.
- ⚠️ **Don't bring gradients or shadows back to create “depth.”** Factory surfaces use contrast, borders, spacing, and type.
- ⚠️ **Don't put the same enumeration in §3 Goals AND §5 Decisions.** Pick the canonical home (usually a decision card) and forward-reference from elsewhere.
- ⚠️ **Don't remove `.decision dd { grid-column: 2 }`.** Without it, `dd` falls under `dt` instead of into column 2. Most browsers won't warn.
- ⚠️ **Don't revert the auto-hide TOC** (`nav.toc` → 68px rail expanding to 248px on hover) **to a sticky 220px sidebar.** Content reads worse with the sidebar always present. Don't shrink the rail below 68px either — 56px clips "VIII" to "VII".
- ⚠️ **Don't hotlink auth-gated assets** (GitHub `user-attachments` images, private CDNs) — they 404 from gistpreview. Inline base64 per [Embedding diagrams (raster)](#embedding-diagrams-raster).
- ⚠️ **Don't inline excalidraw/vector diagrams as base64 PNG.** A handful at `-s 2` push the doc past the gist API's ~1 MB truncation limit; gistpreview then renders only partway through with no error. Use SVG renders — see [Embedding diagrams (raster)](#embedding-diagrams-raster).
- ⚠️ **Don't make a secret-gist URL public-shareable** without confirming with the user. The doc may reference internal Linear tickets, employees, or unmerged architecture.

## References

- `references/template.html` — full Factory-themed HTML scaffold to copy, with RFC components and an optional memo proof band.
- `references/screenshot.js` — Playwright capture. `node screenshot.js <abs-path-to-html> [out-dir]`.
- `references/inspect.js` — DOM probe for layout debugging. `node inspect.js <abs-path> "<selector>"`.
