---
name: ticket-branch
description: Shared atom for creating or resolving a Linear ticket and checking out a clean branch. Background knowledge for workflow commands -- not invoked directly.
---

# Ticket + Branch

## Resolve or Create Ticket

- **Ticket ID provided** (e.g., `TEAM-123`): fetch it with comments and direct
  lineage.
  ```bash
  linear i get <ID> --output json --comments
  linear rel list <ID> --output json
  ```
  If the ticket details or relation list names direct parent/child tickets, fetch
  each one hop:
  ```bash
  linear i get <RELATED_ID> --output json --comments
  ```
  Extract parent goal, child scope boundaries, inherited acceptance criteria,
  constraints, and discussion context. Do not chase deeper hierarchy unless the
  ticket explicitly depends on it. Use the provided ticket for branch naming.
- **No ticket**: create one.
  Team: the repo's ticket routing guide decides, when it has one. Find it at the
  default branch's tip and read it there:
  ```bash
  git ls-tree -r --name-only origin/HEAD | grep -iE '(routing|triage)[^/]*\.md$'
  git show origin/HEAD:<path>
  ```
  Without one, pick from `linear t list --output json --compact --fields key,name`.
  Default priority: 3 (medium).

  **Write a meaningful description** before creating. The description should include:
  - **What**: 1-2 sentences on the problem or feature.
  - **Why**: Context on motivation (bug report, user feedback, tech debt, etc.).
  - **Acceptance criteria**: Concrete conditions for "done" (when known).

  If the user mentions a parent issue or epic, search for it:
  ```bash
  linear search issues "<keywords>" --output json --compact --fields id,identifier,title
  ```
  Then link via `--parent <parent-ID>` when creating.

  ```bash
  ID=$(linear i create "<title>" -t <TEAM> -p <priority> -d "<description>" --id-only --quiet)
  ```

Extract from the ticket identifier:
- **Team prefix**: the letters before the dash (e.g., `ENG`).
- **Issue number**: the digits after the dash (e.g., `456`).

## Create Branch

```bash
DEFAULT_BRANCH=$(git remote show origin 2>/dev/null | awk '/HEAD branch/ {print $NF}')
git fetch origin
git checkout -b "<owner>/<prefix>-<number>-<stub>" "origin/$DEFAULT_BRANCH"
```

- Derive `<stub>` from the ticket title: lowercase, hyphenated, ASCII-only.
- **Full branch name must be <= 32 characters.** Truncate the stub to fit.
- Replace `<owner>` with your branch namespace.
- Example: `ENG-456 "Fix onboarding tooltip"` -> `team/eng-456-fix-onboard`


