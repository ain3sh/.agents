---
name: update-skill
description: Reflect on session learnings and update a skill so future agents succeed without prior context. Use when the user asks to update or refine a skill, or when this session surfaced dead ends, correct pathways, or coverage gaps worth capturing.
argument-hint: <skill-name> [context about what was learned]
---

# Update Skill

Goal: a future agent with **no prior context** acts correctly at minimum tokens read.

## 1. Reflect

Review the session's work (or `$ARGUMENTS`). Identify:

- **Correct pathways**: approaches/commands/patterns that ultimately worked.
- **Dead ends**: what looked promising but failed, and why.
- **Missing info**: what the skill should have covered but didn't.
- **Key insights**: non-obvious learnings that save future agents significant time.

## 2. Read whole, in aggregate

Read **every** file of the skill -- `SKILL.md`, `references/**`, `scripts/**`,
`templates/**` -- fully, before any edit. Surgical patches without the aggregate
view leave incoherence: a command renamed in one section stays stale in another.
Verify behavior claims against the current scripts/tools they describe, not
against memory or the old prose.

## 3. Update

- Fix incorrect or outdated instructions.
- Add the correct pathways from step 1; explicitly mark dead ends with warnings.
- Fill coverage gaps; remove misleading content.
- No filler: every sentence must change what an agent does or prevents a mistake.

## 4. Structure for action

`SKILL.md` is a lean, action-first entrypoint. Target shape, in order:

1. One framing sentence -- the mental model.
2. **Act**: goal → command table. Commands before explanations, always.
3. **Detect**: when/where the skill applies, as a runnable check.
4. **Rules**: numbered, few, each one violation-shaped ("never X -- consequence").
5. **Failure map**: symptom → action table; every row resolves in one command or one reference hop.
6. **References**: explicit `references/<file>.md` pointers with one-line scopes, prefixed "load on demand; do not reabsorb into this file".

Push depth down: per-command internals, env-var tables, safety rationale, and
multi-step edge-case walkthroughs live in `references/*.md`, loaded only when
needed. Split when `SKILL.md` mixes action with explanation or grows past ~80
lines; don't manufacture references for a skill that fits lean in one file.

Restructure invariants:

- **Zero content dropped**: every fragment of the old skill maps to exactly one new home. Diff old against new to prove it.
- **Frontmatter `description` is the trigger**: byte-identical unless the trigger itself is what changed. When it is: descriptions load into **every** session, so each word is a global tax -- name the triggering moments verb-first, far fewer words.
- **One owner per fact**: state each warning/mechanism once, point to it elsewhere. Duplication is where staleness breeds.

## 5. Critique & refine

**Round 1**: Read the result as a fresh agent. Clear? Complete? Would you succeed following only this? Fix.

**Round 2**: Check redundancy, ambiguity, missing edge cases, inconsistent formatting, ordering, and that the section shapes of step 4 held. Fix.

**Final round**: Critique holistically, x2 -- each pass must convey the same information *more effectively*, in *action-oriented language*, with *far fewer words* -- until you are happy with and proud of the work you've done <3
