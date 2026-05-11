---
description: Reflect on session learnings, update a skill, then open a PR
argument-hint: <skill-name> [context about what was learned]
---

## 1. Reflect

Review the work done in this session (or as described in `$ARGUMENTS`). Identify:

- **Correct pathways**: What approaches/commands/patterns ultimately worked?
- **Dead ends**: What looked promising but failed? Why?
- **Missing info**: What did the skill not cover that it should have?
- **Key insights**: Non-obvious learnings that would save future agents significant time.


## 2. Read Current Skill

- Read the current skill file(s) thoroughly.
- Identify: gaps, inaccuracies, outdated information, missing edge cases, misleading guidance.

## 3. Update Comprehensively

Rewrite/amend the skill so that a future agent with **no prior context** would succeed:

- Fix incorrect or outdated instructions.
- Add the correct pathways discovered in step 1.
- Explicitly mark known dead ends with warnings.
- Fill gaps in coverage.
- Remove or update any misleading content.
- Keep the skill focused and actionable -- no filler.

## 4. Critique & Refine

**Round 1**: Read the updated skill as a fresh agent. Is it clear? Complete? Would you succeed following only these instructions? Fix any issues.

**Round 2**: Check for redundancy, ambiguity, missing edge cases, inconsistent formatting, and ordering. Fix any issues.

**Final Round**: Critique and refine holistically, x2, including optimizing for information density per token so we are not bloating the content/size(s) needlessly, till you are happy with and proud of the work you've done <3
