---
description: Implement a Linear ticket -- explore, plan, spec, then code
argument-hint: <TICKET-ID or pasted ticket content>
---

Load skills: **linear-cli**, **quality-ship**.

## 1. Understand the Ticket

- If `$ARGUMENTS` contains a ticket ID (e.g., `TEAM-123`), fetch it:
  ```bash
  linear i get <ID> --output json --comments
  ```
- If pasted ticket content is provided, parse it directly.
- Identify: the problem statement, acceptance criteria, constraints, linked issues/PRs, and any discussion context.

## 2. Explore Current Code

- Use search tools (Grep, Glob, codebase_search) to find all relevant code areas.
- Read the key files: entry points, data models, services, components, tests.
- Map the current behavior and data flow in the area of change.
- Identify existing patterns, conventions, and abstractions to follow.
- When the ticket names specific flows or commands to reuse, trace each one end-to-end and note exactly where the new feature's behavior diverges.
- Note tests, types, configs, and documentation that will need updating.

### Bug-fix tickets: reproduce before proposing a fix

When the ticket describes a bug, confirm you can reliably trigger it before moving to Step 3:

- Identify or write a minimal repro (test case, script, or manual steps) that demonstrates the failure on the current base branch.
- Document the observed vs. expected behavior and the exact conditions that trigger it.
- If reproduction fails, revisit exploration -- a bug you can't trigger is a bug you don't yet understand.

The fix approach in Step 3 should flow directly from the reproduction: explain *which part of the repro breaks* and *why the proposed change stops it from breaking*.

## 3. Think Through the Approach

Do **not** take the easiest-but-ugly path. Evaluate the implementation against:

- **Clean architecture**: Proper separation of concerns, single responsibility.
- **Pattern consistency**: Matches how the rest of the codebase does similar things.
- **Error handling**: Covers failure modes, provides useful error messages.
- **Edge cases**: Boundary conditions, empty states, concurrent access.
- **Testability**: Changes are easy to unit/integration test.
- **Blast radius**: Minimize files changed; avoid unnecessary refactors.
- **Composition over extraction**: Before introducing a new helper or wrapper, check whether the feature can be implemented by entering an existing flow at a different point. Routing through existing plumbing is the default; new plumbing is fine when the existing flow has side effects you don't want, or when direct composition would create worse coupling than a small new abstraction -- but the spec must say why.

If there are multiple viable approaches, evaluate trade-offs explicitly.

## 4. Present Spec

Present a structured implementation plan:

- **Approach**: High-level strategy and rationale for the chosen path.
- **Files to modify/create**: List with a brief description of the changes per file.
- **Key decisions**: Non-obvious choices and their reasoning.
- **Risks**: Potential issues, migration concerns, or things to watch.
- **Alternatives rejected**: At least one simpler approach (e.g., composing an existing flow directly) with a concrete reason it was insufficient.
- **Open questions**: Anything ambiguous that needs user input.

**Wait for user approval before writing any code.**

If questions arise during exploration, ask them immediately -- do not guess at requirements.

## 4b. Bug-fix: regression test (red-green)

After spec approval, before implementing the fix, write an e2e test that captures the broken behavior.

### Write the test

- The test should exercise the **real user-facing flow** that broke -- informed by root cause and fix path from the spec, not just the surface symptom.
- Test the **behavior**, not the implementation detail. This makes it a durable regression guard rather than something coupled to today's code.
- Confirm the test **fails** on the current (unfixed) code.

### After implementing the fix

- Re-run the test. Confirm it **passes**.

### When to skip

Not every bug has an e2e-testable surface. If a non-contrived e2e test isn't feasible, you must justify the skip:

- No e2e test harness exists in the project.
- The bug is in a layer e2e can't reach (race conditions, infra, build-time issues).
- An e2e test would be contrived -- testing an artificial scenario rather than a real user flow.

When skipping, fall back to the narrowest viable alternative: integration test, unit test, or the ad-hoc repro from step 2. State which fallback was used and why.

Record the skip in the PR's **Root Cause Analysis** section (see pr-description): what was attempted, why e2e wasn't viable, and which fallback was used.

## 5. Validate

After implementation is complete and working, **re-load the quality-ship skill** and strictly follow its guidance:

- Detect and run **every** applicable validator (format, lint, knip, typecheck, tests).
- Scope correctly in monorepos (turbo or per-package).
- Check for worktree context and symlink dependencies if needed.
- Fix all issues and re-run until clean.

Do not skip this step or defer it to a follow-up command. The implementation is not done until validators pass.
