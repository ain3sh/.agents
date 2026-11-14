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

## 6. Replay

A reread shows the text is clear, not that an agent acts on it. Commit, push, and report first, calling the edit unproven: a replay never holds the reply. Then size the run to the edit:

| The edit | Run |
|---|---|
| Rewords, moves, or cuts text and changes no decision | Nothing. |
| Changes a decision (a rule, a step, a ranking, the trigger) | One run of the scenario it was written from. The control is the Baseline in the skill's `replay.md`; run one only when none is recorded. |
| Adds a skill, or claims it works beyond that scenario | A control, and a scenario it was not tuned on. |

Run more only when the user asks or a run contradicts the Baseline.

- Give fresh subagents one short brief and a copy of the skill, without its `replay.md`, to read by path, not through the Skill tool. A control (the old revision, or no skill when it is new) differs only in the skill: without one, the skill takes credit for what the model does anyway.
- Name nothing after its arm. A path, branch, or task description that says `control` or `old` tells the run which arm it is.
- Have each run that reads the skill list where it was unclear, wrong, or in the way, quoting the line. Edit from those lines.
- Grade what the runs did (the diff, the decisions in the log) against the control, never their reports or the skill's wording. A run that did what the control did means the edit changed nothing: return to step 3.
- When a run's result was written into the skill, rerun without it before crediting the edit: otherwise the skill is reading its own answer.
- Keep the skill's `references/replay.md` current: Scenarios (prompt and expected result), Grading (check and pass), Baseline (what each arm did, and what was not run). Report the same per arm.

## References

Load on demand; do not reabsorb into this file:

- `references/replay.md`: the scenario, grading, and baseline for edits to this skill.
