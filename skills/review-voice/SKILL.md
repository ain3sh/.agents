---
name: review-voice
description: Reviewer-voice norms for code review -- opinion license, judgment criteria, severity taxonomy (incl. `opinion` tier), and unprompted-opinion sweep. Background knowledge for review-flow commands -- not invoked directly.
user-invocable: false
---

# Review Voice

What to opine on, when to push back, and the final sweep that catches opinions you almost withheld.

## Opinion license

**If you'd push back on this in your own PR, push back here.** Architecture, naming, redundancy, abstraction shape, footgun-shaped APIs, single-canon violations -- voice opinions even when nothing is "broken." Strong design taste and craft pushback are first-class findings, not noise.

The `/review-pr` → `/post-review` split is your safety net: nothing reaches GitHub until the user signs off at the `/review-pr` approval gate. They can drop, reword, or re-severity anything; they cannot recover an opinion you withheld. **Optimize for surfaced opinions over filtered silence.** "Not a bug" → land as `opinion`. "Author probably knows" → still land it; they can dismiss in one line. "Might be wrong" → state the position with the uncertainty.

## Judgment criteria

Phrase as **claims, not questions** -- *"this name reads as X but does Y"* beats *"consider renaming."*

1. **Goal achievement** -- do the changes match the PR's claim? Name gaps.
2. **Architectural opinion** -- if the shape burdens future change, say so. Name the load-bearing assumption, the leak, the fragile coupling. *"This composes badly because X"* beats *"consider whether this composes well."*
3. **Single-canon preservation** (load **single-canon**) -- dual-shape code, fallback adapters, parallel implementations, "compat" branches, coercions guarding old shapes. Cite the canonical path that should remain.
4. **Craft & footguns** -- misleading names, abstractions at the wrong layer, APIs that invite misuse, "clever" code, premature or missing genericity, swallowed errors.
5. **Broader impact** -- name the scenario (*"if request arrives during reconnect, X"*), not the category (*"race possible"*).
6. **Test coverage** -- opine on what the missing test would catch, not just that one is missing.

## Severity taxonomy

| Tier | Meaning (author response) |
|---|---|
| `critical` | Defect blocking merge -- correctness, security, data loss, regression (must fix) |
| `warning` | Significant defect or near-defect that will burn a future reader (address or defend) |
| `opinion` | Judgment-grade pushback -- design, architecture, craft, taste. Not a defect claim; a position you hold and want the author to engage with (engage; disagreement is fine, dismissal-by-silence isn't) |
| `suggestion` | Recommended improvement, lighter than `opinion` (consider) |
| `nit` | Cosmetic / pure preference (optional) |

**Calibration:** *"I'd push back in my own PR"* → at least `opinion`. *"Footgun"* → `warning` if likely to fire, `opinion` if structural. *"Violates single-canon"* → `opinion` minimum. **Always state the *why*** -- a tier-tagged claim without rationale reads as drive-by; the author can't engage.

## Unprompted-opinion sweep

After running the criteria, ask: *"What would I say about this PR if asked freely, without a checklist in front of me?"*

Add anything that surfaces as a finding at the right tier. Common catches: "I'd have factored differently" (`opinion`), "author reaches for X when Y is the codebase idiom" (`opinion`), "layering feels off but I can't pin one line" (`opinion` on the most representative line, broader concern in body).

Silence at this stage must be **justified** -- if you can't name why you're not voicing a thought, voice it.
