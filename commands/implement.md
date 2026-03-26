---
description: Implement a Linear ticket -- explore, plan, spec, then code
argument-hint: <TICKET-ID or pasted ticket content>
---

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
