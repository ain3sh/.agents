---
description: Reflect on session learnings, update a skill, then open a PR
argument-hint: <skill-name> [context about what was learned]
---

Load skills: **ticket-branch**, **quality-ship**.

## 1. Reflect

Review the work done in this session (or as described in `$ARGUMENTS`). Identify:

- **Correct pathways**: What approaches/commands/patterns ultimately worked?
- **Dead ends**: What looked promising but failed? Why?
- **Missing info**: What did the skill not cover that it should have?
- **Key insights**: Non-obvious learnings that would save future agents significant time.

## 2. Ticket + Branch

Follow the **ticket-branch** skill:
- Create a ticket titled "Update <skill-name> skill with learnings".
- Check out a new branch.

## 3. Read Current Skill

- Read the current skill file(s) thoroughly.
- Identify: gaps, inaccuracies, outdated information, missing edge cases, misleading guidance.

## 4. Update Comprehensively

Rewrite/amend the skill so that a future agent with **no prior context** would succeed:

- Fix incorrect or outdated instructions.
- Add the correct pathways discovered in step 1.
- Explicitly mark known dead ends with warnings.
- Fill gaps in coverage.
- Remove or update any misleading content.
- Keep the skill focused and actionable -- no filler.

## 5. Critique & Refine (x2)

**Round 1**: Read the updated skill as a fresh agent. Is it clear? Complete? Would you succeed following only these instructions? Fix any issues.

**Round 2**: Check for redundancy, ambiguity, missing edge cases, inconsistent formatting, and ordering. Fix any issues.

## 6. Quality + Ship

Follow the **quality-ship** skill:
- Run all detected quality checks on changed files.
- Commit with message: `docs(<skill-name>): update with learnings from <context>`.
- Push and open PR.

PR body should describe: what was learned, what changed in the skill, and why it improves future agent success.

Report the PR URL.
