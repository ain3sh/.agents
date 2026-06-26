# Visual evidence — live proof of a concrete visual change

When a PR changes what a human *sees*, the prose and the diff are both second-hand accounts. **Live proof is the crux of the reviewer's trust layer** — a screenshot or clip from the running app turns "I'll take your word for it" into "I can see it works," collapsing a checkout-build-click loop into a glance. Earn it honestly: a missing, faked, or sanitized artifact is worse than none.

## When this fires

The diff makes a **concrete visual change** a reviewer would otherwise have to build and run to see:

- Web / Electron UI — a component, page, layout, style, or animation
- Terminal TUI / CLI output — Ink/chalk renders, tables, spinners, a new command's output
- Rendered media — generated images, diagrams, exported docs
- Native desktop GUI

It does **not** fire for logic / backend / config changes with no visible delta, or refactors that preserve the exact rendering (those lean on Verification prose, plus a diagram via `references/artifacts.md` when structure moved). If you can't name the on-screen difference a reviewer would look for, there's nothing to capture — skip the section, don't manufacture a clip.

## Timing — after the PR is open, never blocking it

Capture is multi-minute (launch, script the interaction, record, optionally render, upload), so **never block `gh pr create` on it.** Open the PR with the prose body first; *then* run this workflow and PATCH the artifact high into the body — that's a refresh, so `references/refresh.md` owns the write and marker re-stamp. The artifact is a fast follow-up, not a gate on the initial push.

## Capture engine — droid-control

Load the **droid-control** skill and let it route — it owns the *how* (drivers, recording, layout, polish, verification); this file owns the *what* and *why* for a reviewer:

- **Target** — web/Electron → agent-browser; terminal TUI/CLI → tuistory (default) or true-input (only when real-emulator rendering fidelity is itself what changed); native GUI → desktop-control.
- **Layout** — `single` by default; `side-by-side` only for a *real* before/after (regression, restyle, parity-preserving refactor) — capture old and new branches with identical interactions. Never fake a baseline to justify the split.
- **Stage** — capture → (compose) → verify.

## The decision tree

Three calls, in order. Bias each toward the *smallest artifact that fully answers the reviewer's question* — surplus polish and length bury the signal.

### 1. Still vs motion

| Pick | When |
|---|---|
| **Screenshot** (or before/after pair) | the proof is a *state* read at a glance — new layout, restyle, a fixed rendering glitch, new static output |
| **Video** | the proof is *behavior over time* — animation, transition, an interaction flow, spinner/progress, a multi-step TUI session |

Litmus: *can one frame carry it?* If yes, never reach for video — a still is cheaper, smaller, inline-renders, and pairs cleanly as before/after. A still of a motion change is a lie by omission; a video of a static change is dead weight.

### 2. Raw vs showcase (video only)

| Pick | When |
|---|---|
| **Raw clip** (no chrome — the default) | routine reviewer evidence: honest, fast, exactly what a reviewer verifies against |
| **Showcase** (droid-control preset + props) | the PR *is* the showcase — a hero feature, a README/demo deliverable, content for external eyes (release notes, social, landing) |

When in doubt, raw — a cinematic preset on a routine bugfix costs render time and buries the change. If you do go showcase, match the register: `macos` / `minimal` for internal clips, `factory` / `factory-hero` only for genuinely Factory-branded external content; add a keystroke overlay only when the *inputs* are part of the proof.

### 3. What to show

Answer the reviewer's actual question, nothing more:

- **The changed surface in the real app**, with just enough context to be legible and zero dead time.
- **Fix** → the broken path now working (side-by-side: the break on old).
- **Feature** → the primary happy path it exists for.
- Hold each changed state 2-3s so it reads; verify between steps — a snapshot proving *nothing happened* is also evidence.
- **Caption every artifact** (per `references/artifacts.md`): capture conditions, what to watch, a quantified delta where one exists. An uncaptioned clip is net-zero.

## When the capture finds a bug — fail loud

Live capture runs the real code — it's the most honest test you'll run, and it can reveal the change doesn't work, regresses something adjacent, or throws. The rule is absolute:

- **Never pick a cleaner take, trim around the failure, or drop to a screenshot to dodge it.** The artifact's whole value is that it's real; hiding a real failure corrupts the trust layer worse than no evidence.
- **Stop and surface it loudly** to the user; don't attach a misleading artifact, and treat it as a blocker on the PR's claims.
- **Triage harness vs product first** — a driver timeout, missing color env, or viewport letterbox is a capture flake; recover and retry per droid-control before escalating, and only a failure that reproduces in the product counts as a bug.
- **Real bug → RCA it.** Load **root-cause-analysis**, trace to the first unintended side effect, fix it, and thread the result into the PR (Root Cause Analysis / Side Effects / Verification). Fixing what the camera caught is the line between evidence and theater.

## Placement & upload

- **High in the body** — its own `## Visual Evidence` heading right after Architecture, or after Description when there's no diagram (fold into `## Architecture` if a diagram is already there). Reviewers meet the proof before the diff.
- **Screenshot** → `gh-attach --md file.png` for inline markdown; pair before/after stacked or as a two-row table, each captioned.
- **Video** → GitHub inlines an mp4/webm only when the bare `user-attachments` URL is on its own line, so use `gh-attach --url clip.mp4` and paste that URL alone (markdown image syntax does **not** embed video). Keep under 5 MB (25 MB hard limit).
- Upload mechanics, headless-cookie fallback, and the never-commit / never-`raw.githubusercontent` / never-secrets rules live in `references/artifacts.md` — don't re-derive.

## Verification handoff

- Run droid-control's **verify** atom: the artifact plays, hits target resolution, fits the size/duration budget, and every claimed change has visible evidence.
- Tie it to a **Verification → Behavior verified** line anchored with `verified @ <sha>`, so prose and proof check each other and a refresh can flag the clip stale when the captured path changes.
