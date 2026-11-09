---
name: update-skill
description: "Use when the user asks to update or refine a skill, or when a session surfaced dead ends or correct pathways worth capturing in one."
argument-hint: "<skill-name> [context about what was learned]"
---

# Update Skill

Goal: an agent with no prior context acts correctly after reading the fewest tokens.

## 0. Load

Load before drafting any edit. **harness-optimization** always: the layer at fault may not be this skill. Then each that applies, unless already active:

| Moment | Load |
|---|---|
| Cause of the misbehavior not yet named | **root-cause-analysis** |
| Skill or its neighbors not yet mapped | **zoom-out** |
| Edit touches a command, flag, config key, or rule other files rely on | **single-canon** |
| Candidate edits or layers compete (this skill, another skill, AGENTS.md, a hook) | **patch-coherence** |

## 1. Reflect

From the session (or `$ARGUMENTS`), list what worked, what failed and why, what the skill lacked, and non-obvious insights.

## 2. Read whole

Read every file of the skill (`SKILL.md`, `references/**`, `scripts/**`, `templates/**`) before editing; a partial view leaves stale copies elsewhere. Verify behavior claims against the current scripts and tools, not memory or old prose.

## 3. Update

- Fix wrong or stale instructions; delete misleading ones.
- Write each fix as the shortest linear instruction: do X; if it fails, do Y.
- Name a dead end only if an agent would otherwise take it.
- Every sentence must change what an agent does.

## 4. Structure

`SKILL.md` is a lean, action-first entrypoint, in order:

1. One framing sentence: the mental model.
2. **Act**: goal → command table, commands before explanations.
3. **Detect**: when the skill applies, as a runnable check.
4. **Rules**: few, each violation-shaped ("never X: consequence").
5. **Failure map**: symptom → action; each row resolves in one command or one reference hop.
6. **References**: `references/<file>.md` pointers with one-line scopes, prefixed "load on demand; do not reabsorb into this file".

Move internals, env-var tables, rationale, and edge-case walkthroughs to `references/*.md`. Split when `SKILL.md` mixes action with explanation or passes ~80 lines; a skill that fits lean in one file stays one file.

Invariants:

- **Zero content dropped** on a restructure: diff old against new; every fragment has exactly one new home.
- **Frontmatter `description` is the trigger**: byte-identical unless the trigger changed. It loads into every session, so name the triggering moments verb-first, in few words.
- **One owner per fact**: state it once, point to it elsewhere.

## 5. Cut before committing

1. Read the result as a fresh agent: could you succeed with only this? Fix gaps, ambiguity, and drift from step 4's shape.
2. Read the diff. Delete every added line that doesn't change what an agent does; shorten the rest. Repeat until nothing is left to remove.
