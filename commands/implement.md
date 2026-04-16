---
description: Implement a Linear ticket -- explore, plan, spec, then code
argument-hint: <TICKET-ID or pasted ticket content>
---

Load skills: **linear-cli**, **worktree-setup**, **quality-ship**. Bug-fix tickets also load: **root-cause-finder**, **step-through**, **consolidate-test-suites**.

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

### Bug-fix tickets: root-cause analysis before proposing a fix

When the ticket describes a bug, apply the **root-cause-finder** methodology before moving to Step 3:

1. **Reproduce**: Identify or write a minimal repro (test case, script, or manual steps) that demonstrates the failure on the current base branch. If reproduction fails, revisit exploration -- a bug you can't trigger is a bug you don't yet understand.

2. **Trace root cause**: Do not stop at the first error. Follow the root-cause-finder workflow:
   - State the expected behavior and invariant in plain language.
   - Trace the causal chain from intended action to observed effect.
   - Ask whether the request or mutation should have happened at all.
   - Find the first unintended side effect -- that is the root cause, not the downstream error.
   - Audit hidden writes: lifecycle hooks, subscribers, watchers, background jobs, persistence restore, cache refreshers.

3. **Step through** (when applicable): If the bug involves multi-actor sequencing, async callbacks, background refreshes, recovery paths, queues, retries, or state machines, apply the **step-through** skill: walk the broken flow with explicit state (`actor = {...}`) at every transition, taking each actor's perspective, until an invariant breaks. Do not skip to "walk the fix" -- step through the broken flow first.

The fix approach in Step 3 should flow directly from the root-cause analysis: explain *what the first unintended side effect is*, *which part of the repro breaks*, and *why the proposed change stops it from breaking*.

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

After spec approval, before implementing the fix, apply the **consolidate-test-suites** skill to decide where the test belongs, then write it.

### Place the test

Before writing any test code, run the consolidate-test-suites decision process:

1. **Name the invariant** -- the rule that must stay true.
2. **Pick the owning layer** -- the lowest layer (unit, integration, or e2e) that truly owns and can prove the invariant. If torn between unit and integration, choose integration. Never choose e2e to compensate for uncertainty.
3. **Find the canonical suite** -- prefer adding to an existing test file in the owning layer over creating a new file. Follow the decision order: existing test > new test in existing file > new file in canonical suite > standalone regression (exception rule only).

### Write the test

- The test should exercise the **real user-facing flow** that broke -- informed by root cause and fix path from the spec, not just the surface symptom.
- Test the **behavior**, not the implementation detail. This makes it a durable regression guard rather than something coupled to today's code.
- Place it in the canonical suite identified above.
- Confirm the test **fails** on the current (unfixed) code.

### After implementing the fix

- Re-run the test. Confirm it **passes**.
- Search for tests that assert the same invariant. Keep the strongest owned location, merge unique assertions, delete or simplify weaker duplicates.

### When to skip

Not every bug has a testable surface. If a test isn't feasible, you must justify the skip:

- No test harness exists in the project for the owning layer.
- The bug is in a layer tests can't reach (race conditions, infra, build-time issues).
- A test would be contrived -- testing an artificial scenario rather than a real flow.

When skipping, fall back to the narrowest viable alternative: the next lower layer, or the ad-hoc repro from step 2. State which fallback was used and why.

Record the skip in the PR's **Root Cause Analysis** section (see pr-description): what was attempted, why testing wasn't viable, and which fallback was used.

## 5. Validate

After the draft implementation is complete and before running any validators:

### 5a. Worktree pre-check (mandatory, runs first)

**Re-load the worktree-setup skill** and check for worktree context:

```bash
MAIN_REPO=$(git worktree list | head -1 | awk '{print $1}')
[ "$(git rev-parse --show-toplevel)" != "$MAIN_REPO" ] && echo "WORKTREE -- follow worktree-setup before validators"
```

If in a worktree (or the working directory path contains `worktree`), follow the skill to mirror `node_modules` / repoint workspace packages / symlink `.venv` **before** touching any lint, typecheck, knip, or test command. Validators run in a bare worktree will either fail with missing-module errors or quietly resolve to stale main-repo sources -- both waste a full cycle and leave a botched symlink state for `/open-pr` to clean up later.

Do not treat this as optional. Running it here means `/open-pr` can trust the environment is already correct.

### 5b. Quality-ship

Once the environment is ready, **re-load the quality-ship skill** and strictly follow its guidance:

- Detect and run **every** applicable validator (format, lint, knip, typecheck, tests).
- Scope correctly in monorepos (turbo or per-package).
- Fix all issues and re-run until clean.

Do not skip this step or defer it to a follow-up command. The implementation is not done until validators pass.
