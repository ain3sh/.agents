---
name: structural-review
description: Shared atom for structural maintainability judgment on a diff -- hunt code-judo simplifications, spaghetti-condition growth, file-size explosions, and orchestration smells. Background knowledge for review and self-review flows -- not invoked directly.
user-invocable: false
---

# Structural Review

Correctness review asks "does this work, at the right layer?" This atom asks what comes after: **is there a reframing of the same behavior that makes the implementation dramatically simpler?** A diff can be root-cause-correct and slop-free yet leave the codebase messier than the obvious alternative shape.

Be ambitious. "This could be a bit cleaner" is not the bar. Hunt **code-judo moves**: behavior-preserving restructurings where whole branches, helpers, modes, flags, or layers disappear because the change is framed against the existing architecture instead of bolted onto it. Prefer the version that feels inevitable in hindsight; when complexity can be deleted rather than rearranged, push for deletion.

## Boundary with sibling skills

This atom owns the simplification hunt and the structural tripwires. It does not own:

- **Severity** -- `voice` owns the canonical taxonomy; map into it (below), never a local blocker tier or separate approval bar.
- **Mechanical smells** -- thin wrappers, pass-through helpers, generic casts, duplicate signatures are `slop-scan`'s; don't hand-audit them, and when both fire on a line keep one finding.
- **Legacy-path deletion** -- compat branches, dual shapes, fallback adapters are `single-canon`'s.

## The hunt

For every meaningful change, ask -- and when the answer is yes, suggest the move that deletes complexity, not the one that polishes it:

- Can this be reframed so fewer concepts, branches, or helper layers exist at all?
- Would a different state model make the new conditionals vanish instead of getting centralized? Could a typed model or explicit dispatch replace the condition chain?
- Would moving the ownership boundary let an existing abstraction absorb the feature instead of grafting onto it?
- Is each new abstraction earning its keep, or is it indirection spreading the same complexity around? Delete the layer rather than polish it.
- Did a cohesive module become more coupled, more stateful, or harder to scan?
- Can special cases collapse into a simpler default flow with fewer exceptions?

A refactor that moves complexity without reducing the number of concepts a reader must hold is not an improvement; say so.

## Tripwires

Design problems, not stylistic nits:

- **File-size explosion.** The PR pushes a file past ~1k lines. Presumptively ask for decomposition first; waive only for a compelling structural reason with the result still clearly organized.
- **Spaghetti growth.** New ad-hoc conditionals, one-off booleans, nullable modes, or special-case branches inserted into unrelated or already-busy flows; edge cases handled mid-function instead of behind their own seam.
- **Boundary leaks.** Feature checks scattered across shared paths; implementation details leaking through an API; logic in the convenient layer instead of the owning one; a bespoke near-duplicate of a canonical helper.
- **Contract muddying.** New optionality, `any`/`unknown`, casts, or ad-hoc object shapes where an explicit typed boundary would simplify the control flow; silent fallbacks papering over an unclear invariant.
- **Orchestration smells.** Independent work serialized for no reason; related updates that can leave state half-applied when an atomic structure is available; orchestration tangled into the logic it sequences. Flag brittleness, not micro-optimizations.
- **"Temporary" branching** with no removal path -- it calcifies into permanent debt.

## Severity and scope

Fold findings into the `voice` taxonomy:

- **`warning`**: a structural regression that will burn future readers -- file-size explosion, spaghetti growth in a shared flow, boundary leak, half-applied-state failure mode.
- **`opinion`**: a missed code-judo move, an abstraction not earning its keep, needlessly sequential orchestration. State the concrete alternative shape; a tier without the reframing is a drive-by.
- Code the diff doesn't touch caps at `opinion`, and only when the diff makes it worse. Don't demand out-of-scope refactors; if the cleanup deserves its own PR, say that.

Few high-conviction findings beat a flood. "Maybe rename this" when the real issue is structural is the failure mode; so is blessing a merely cleaner version of a messy idea when a much simpler idea is visible. In review flows this is flag-not-fix: name the smell and the reframing, let the author execute. In self-review flows, apply the remedy directly.
