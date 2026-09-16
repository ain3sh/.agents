# Review Judgment

## Opinion license

**If you'd push back on this in your own PR, push back here.** Architecture, naming, redundancy, abstraction shape, footgun-shaped APIs, single-canon violations: voice opinions even when nothing is "broken". Design taste and craft pushback are first-class findings, not noise.

An edit-and-approval gate always stands between you and publishing (in the review flow, the `/review-pr` sign-off before `/post-review`). The user can drop, reword, or re-severity anything; they cannot recover an opinion you withheld. **Optimize for surfaced opinions over filtered silence.** "Not a bug" becomes an `opinion`. "Author probably knows" still lands; they dismiss it in one line. "Might be wrong" states the position with the uncertainty attached.

## What to opine on

1. **Goal achievement.** Do the changes match the stated claim? Name the gaps.
2. **Architecture.** If the shape burdens future change, name the load-bearing assumption, the leak, or the fragile coupling.
3. **Single-canon** (load **single-canon**). Dual-shape code, fallback adapters, parallel implementations, "compat" branches, coercions guarding old shapes. Cite the canonical path that should remain.
4. **Craft and footguns.** Misleading names, abstractions at the wrong layer, APIs that invite misuse, "clever" code, swallowed errors, premature or missing genericity.
5. **Broader impact.** Name the scenario (see [craft](craft.md)), not the category.
6. **Test coverage.** Opine on what the missing test would catch, not just that one is absent.

## Severity taxonomy (canonical; other skills defer here)

| Tier | Meaning (author response) |
|---|---|
| `critical` | Defect blocking merge: correctness, security, data loss, regression (must fix) |
| `warning` | Significant defect or near-defect that will burn a future reader (address or defend) |
| `opinion` | Judgment-grade pushback on design, architecture, craft, or taste. Not a defect claim; a position you hold and want engaged (engage; disagreement is fine, dismissal-by-silence is not) |
| `suggestion` | Recommended improvement, lighter than `opinion` (consider) |
| `nit` | Cosmetic or pure preference (optional) |

**Calibration:** *"I'd push back in my own PR"* lands at least `opinion`. *"Footgun"* is a `warning` if likely to fire, an `opinion` if structural. *"Violates single-canon"* is `opinion` minimum. **Always state the *why***: a tier without rationale reads as drive-by, and the author cannot engage it. Tier-to-comment mapping lives in `post-review`; design-grade `opinion`s rarely warrant an apply-clickable suggestion.

## Final sweep

Ask *"What would I say about this if asked freely, without a checklist?"* and add whatever surfaces, at the right tier. Common catches: "I'd have factored differently" (`opinion`), "reaches for X when Y is the codebase idiom" (`opinion`), "layering feels off but I can't pin one line" (`opinion` on the most representative line, broader concern in the body). Silence here must be **justified**: if you can't name why you're withholding a thought, voice it.
