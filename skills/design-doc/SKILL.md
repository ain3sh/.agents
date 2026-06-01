---
name: design-doc
description: Author a publication-grade single-file HTML design doc (RFCs, architecture proposals, sync prep). Editorial typography, decision cards, fact-checked code references, Playwright-verified layout, secret-gist publishing. Use when an engineer asks for a design doc, RFC, monograph, sync-prep brief, or "make this look like a real spec."
---

A design doc here is one self-contained HTML file — fonts via Google Fonts, all styles inline, no JS framework — that reads like a university-press technical monograph. The aesthetic exists to make reviewers actually read it; the structure exists to make the engineer's argument legible.

Output target: ~1.5k–3k lines, ~80–200 KB, prints to A4, dark-mode aware, publishable as a secret gist viewed via `gistpreview.github.io`.

## When to use

- Engineer asks for an RFC, design doc, ADR, monograph, technical spec, or sync-prep brief.
- A PR has architectural weight (≥2 reviewers, multiple sub-decisions) and needs framing beyond the PR description.
- A change touches a contract, persistence, or cross-component ownership and needs one shareable artifact.

**Skip this skill for** short READMEs, Linear ticket bodies, PR descriptions, slide decks, or anything best read in markdown — use markdown instead.

## Process recipe

The order matters. Skipping step 2 is the most common failure: prose ends up referencing constants or call sites that don't exist.

### 1. Frame the argument (plain text, before any HTML)

Name three things:
- **The single structural claim** — one sentence, ≤25 words. This becomes the tagline + §1 lede.
- **The 3–8 key decisions** — each becomes a `D` card with Decision / Rationale / Alternatives rejected / Consequence.
- **The non-goals.** If you can't name 3, the goals are too vague.

### 2. Source-of-truth pass

For every constant, file path, function signature, enum, and limit you intend to cite, run `rg` and verify. Write verified facts to a scratchpad. Two failure modes you will hit if you skip this:
- **Numeric limits.** Prior session caught `LOOP_MIN_INTERVAL_MS` referenced in prose — it didn't exist; the actual guard was `intervalMs < MINUTE_MS` inline.
- **Caps with multiple terms.** Prior session caught "jitter capped at 10%" that should have been "10% of period, capped at 15min."

When the PR description disagrees with the code, **the code wins** and you flag the discrepancy to the user.

### 3. Copy the template

```bash
cp ~/.agents/skills/design-doc/references/template.html <project>/.agents/specs/<slug>-design.html
```

Do not start from scratch. The styles encode hard-won decisions (variable-axis tuning, `text-wrap: balance`, decision-card grid, auto-hide nav, dark mode, print stylesheet). The template is a working scaffold — render it once with the screenshot script in step 5 to confirm it loads before filling.

### 4. Fill the scaffold top-down

Filling top-down keeps prose honest with structure:

1. `<title>`, eyebrow, `h1.title`, `.tagline`, `.meta` strip.
2. **Optional** `figure.demo` if there's a demo video — see [Embedding video](#embedding-video).
3. §1 Summary — `.lede` with `.dropcap` + 1 supporting paragraph (zero-context rules below).
4. §2 Context — reader primer first, then what breaks today (tickets spelled out), why now.
5. §3 Goals & non-goals — `.two-col > .panel`.
6. §4 Proposal — `.pullquote` thesis + `figure.diagram` SVG + prose.
7. §5 Key decisions — `article.decision` × N. **Usually 60–70% of the doc by length.**
8. §6 Tradeoffs — `table.kv` or short prose.
9. §7 Rollout & verification — feature-flag posture, telemetry, rollback.
10. §8 Open questions — `ol.numbered`, **ordered by how much each answer would change the design** (highest leverage first).
11. `.colophon` + `footer.doc`.

Skip a section only if it's genuinely empty for this change — don't pad.

**Write for a reader with zero context (review-tested — violating these draws "hard to read, context implicit and out of order" feedback):**

- **§1 Summary lede = 1–2 sentences a completely new reader understands**: the user-visible problem in plain words, then the fix in plain words. No internal vocabulary that only makes sense after §4 ("separate liveness from commit"-style taglines read as meaningless), and never open with a non-goal ("the visual shape is unchanged") — it buries the why.
- **§2 Context opens with a basics primer** before any deep-dive: define the system being changed and its load-bearing primitives, and define terms the rest of the doc leans on ("monotonic", "idempotent", …) — what they mean *here* and why they matter. Goals/Non-goals must read cleanly using only words the primer introduced.
- **Spell out every motivating ticket in-doc**: bold `ID — symptom` title, then 2–3 sentences of user-visible failure + mechanism. A bare tracker link is not context; the reader must never need to open Linear to follow the argument.
- **Order = how a stranger builds context**: problem → primer → mechanism of failure → concrete failures → goals → proposal. When revising a published doc against reviewer feedback, keep it a controlled change — touch only the sections the feedback targets.

### 5. Iteration loop (mandatory)

Write → capture → inspect → fix:

```bash
node ~/.agents/skills/design-doc/references/screenshot.js <abs-path-to-html>
# → /tmp/doc-previews/scroll-light-NN.png + hero-dark-v2.png
```

Run from a directory whose `node_modules` resolves `playwright` (a repo root that ships it works); from `/tmp` it dies with `ERR_MODULE_NOT_FOUND`.

**Read each PNG with the `Read` tool at `image_quality="high"`.** Fix layout, contrast, and overflow bugs visually before tightening prose. Bugs you will only catch this way:
- `dl > dd` falling under `dt` instead of into column 2 → the template pins `grid-column: 2`; if you copied a card and removed it, restore it.
- Dark-mode contrast failures on `--code-bg` and `--accent-soft`.
- SVG text overflowing on narrow viewports.

If layout is mysterious, run `inspect.js`:
```bash
node ~/.agents/skills/design-doc/references/inspect.js <abs-path> "<css-selector>"
```
It dumps bounding rects + computed styles for the first 12 matches.

### 6. Two content passes

After visual layout is clean:

- **Pass 1 — structural cuts.** If a fact appears in §1 and §5, delete it from §1 and link forward ("full list: D7"). The doc gets *shorter* in this pass, not longer.
- **Pass 2 — polish.** Read aloud (literally — your inner voice catches bumps). Replace neologisms ("due-times" → "task that came due three times"), kill "actually", strip "we can", tighten cross-references. Each Edit should remove or replace text, rarely add.

### 7. Re-verify

Re-run `screenshot.js`. **`scrollHeight` should drop, not grow.** Prior session went 18820 → 18429 px and 17 → 14 segments with no information lost.

### 8. Publish (optional)

See [Publishing](#publishing).

## Aesthetic foundation

The template ships one canonical aesthetic — warm cream paper, oxblood ink, Fraunces + JetBrains Mono. Keep it across docs unless the user explicitly asks otherwise; consistency across the engineer's design docs has more value than per-doc novelty.

To retheme: **change only `:root` custom properties** in both the light and `@media (prefers-color-scheme: dark)` blocks. Leave structural CSS alone.

## Typography craft (the non-obvious wins)

Editorial feel comes from variable-axis tuning per role, not from picking a "nicer serif." The template encodes these — list here so you don't accidentally undo them:

| Role | Variation settings | Note |
|---|---|---|
| `body` | `opsz 16, SOFT 40, WONK 0` + `font-feature-settings: "kern", "liga", "dlig", "onum"` | Old-style numerals are non-negotiable for editorial tone. |
| `h1.title` | `opsz 144, wght 500, SOFT 30` | Big optical size + slight weight = display-cut feel. |
| `.tagline` | `opsz 32, wght 380, SOFT 60`, **`font-style: normal`** | Italic at 18–22px tanks reading speed. |
| `section.block > h3` | `opsz 72, wght 500, SOFT 40` | Forces Fraunces into its display master. |
| `.dropcap` | `opsz 144, wght 500, SOFT 80` + `font-feature-settings: "dlig", "swsh"` | Swash variants are why we use Fraunces and not Georgia. |
| `.pullquote p` | `opsz 48, wght 400, SOFT 50`, italic | Italic IS appropriate at 22–28px display sizes. |
| `em` | `opsz 17, wght 400, SOFT 60` | Slightly softer to differentiate from upright. |
| All mono | `font-feature-settings: "cv02", "cv03", "zero"` | Slashed zero, disambiguated `i`/`l`. |

Use `text-wrap: balance` on every heading, tagline, pullquote, figcaption, and decision title. Use `color-mix(in oklab, var(--accent) X%, transparent)` for tonal blends — don't invent new hex codes.

## Components inventory

All defined in `references/template.html` — read it for any pattern you're unsure of.

| Selector | Purpose | When to use |
|---|---|---|
| `.eyebrow` | Mono uppercase kicker w/ rule | Above titles & figure labels |
| `h1.title` + `.tagline` | Hero | Once, in `header.doc` |
| `.meta .field` | Status/author/reviewers grid | Once, after tagline |
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
| `.colophon` + `footer.doc` | Closing credits + provenance | Once, at end |

**Citing code.** Use `<code>name</code>` for function/component names inline. File paths get one explicit anchor at the point of citation: "(see `apps/cli/src/services/scheduled-tasks/loopSchedule.ts:42`)". Reviewers `rg` from names; they don't click.

## Publishing

For internal docs, **secret gist + gistpreview** is the only path that reliably works without org infra:

```bash
gh gist create <path>/<slug>-design.html --desc "<title>"
# → https://gist.github.com/<user>/<gist-id>
```

Share: `https://gistpreview.github.io/?<gist-id>`

Update: `gh gist edit <gist-id> <path>/<slug>-design.html`

**Revising an already-published doc** — keep the same gist id and filename so the gistpreview link already shared in PRs/Slack stays valid:

```bash
# pull the live copy to revise against (strip tags to a text outline if you only need structure)
gh api gists/<gist-id> --jq '.files["<slug>-design.html"].content' > current.html
# push: content is too large for -f flags; build {"description": ..., "files": {"<name>": {"content": ...}}}
# with a short python script, then
gh api gists/<gist-id> -X PATCH --input /tmp/gist-patch.json
```

The API path also updates the gist description and handles multi-MB files (a ~2 MB doc with inlined images PATCHes and previews fine).

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

1. Render two transparent variants so the diagram inherits the doc's paper/dark background:
   `excalirender d.excalidraw -o light.png --transparent -s 2` and `… -o dark.png --transparent --dark -s 2`.
2. Inside `figure.diagram`, swap themes with `<picture>`:
   `<picture><source srcset="data:image/png;base64,DARK" media="(prefers-color-scheme: dark)"><img src="data:image/png;base64,LIGHT" alt="…"></picture>` + a `<figcaption>`.
3. Add `figure.diagram img, figure.diagram picture { width: 100%; height: auto; display: block; }` beside the existing `svg` rule.
4. Author the HTML with placeholder tokens and inject the base64 with a small python pass — don't paste megabyte strings through editor tools.
5. Size: base64 inflates ~33%; render at the smallest scale that stays crisp and verify both themes with the screenshot loop.

## Verification checklist

Before declaring done:

**Facts**
- [ ] Every cited constant / file path / function signature was verified with `rg` against source.
- [ ] PR description and code agree on numerics; if not, code wins and the discrepancy is flagged.

**Reader**
- [ ] §1 lede passes the zero-context test (plain-words problem + fix, no internal jargon, no leading non-goal).
- [ ] §2 opens with the primer; every motivating ticket is described in-doc — the reader never needs to open the tracker.

**Structure**
- [ ] All eight standard sections present (or skip is justified).
- [ ] Each `article.decision` has all four `dt` slots: Decision, Rationale, Alternatives rejected, Consequence.
- [ ] §8 Open questions are ordered by leverage (highest first).
- [ ] No literal "TODO" or `<!-- TODO -->` markers remain.

**Visual**
- [ ] Light + dark mode tested via Playwright captures; no contrast failures on code blocks or accent chips.
- [ ] Print stylesheet renders without overflow (Chrome → Cmd-P → check pagination).
- [ ] `scrollHeight` after Pass 2 is ≤ `scrollHeight` after Pass 1. If it grew, you bloated.
- [ ] Tagline is `font-style: normal`. (Frequent regression — looks elegant in italic, reads worse.)

## Dead ends (warnings)

- ⚠️ **Don't render only in light mode.** Half of reviewers use dark; the Playwright dark capture catches contrast bugs in 5 seconds.
- ⚠️ **Don't put the same enumeration in §3 Goals AND §5 Decisions.** Pick the canonical home (usually a decision card) and forward-reference from elsewhere.
- ⚠️ **Don't remove `.decision dd { grid-column: 2 }`.** Without it, `dd` falls under `dt` instead of into column 2. Most browsers won't warn.
- ⚠️ **Don't revert the auto-hide TOC** (`nav.toc` → 56px rail expanding to 248px on hover) **to a sticky 220px sidebar.** Content reads worse with the sidebar always present.
- ⚠️ **Don't hotlink auth-gated assets** (GitHub `user-attachments` images, private CDNs) — they 404 from gistpreview. Inline base64 per [Embedding diagrams (raster)](#embedding-diagrams-raster).
- ⚠️ **Don't make a secret-gist URL public-shareable** without confirming with the user. The doc may reference internal Linear tickets, employees, or unmerged architecture.

## References

- `references/template.html` — full HTML scaffold to copy. ~1100 lines, mostly CSS + one example of each component pattern.
- `references/screenshot.js` — Playwright capture. `node screenshot.js <abs-path-to-html> [out-dir]`.
- `references/inspect.js` — DOM probe for layout debugging. `node inspect.js <abs-path> "<selector>"`.
