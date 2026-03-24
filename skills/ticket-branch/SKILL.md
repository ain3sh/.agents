---
name: ticket-branch
description: Shared atom for creating or resolving a Linear ticket and checking out a clean branch. Background knowledge for workflow commands -- not invoked directly.
user-invocable: false
---

# Ticket + Branch

## Resolve or Create Ticket

- **Ticket ID provided** (e.g., `TEAM-123`): fetch it.
  ```bash
  linear i get <ID> --output json
  ```
- **No ticket**: create one.
  ```bash
  ID=$(linear i create "<title>" -t <TEAM> -p <priority> --id-only --quiet)
  ```
  Discover teams with `linear t list --output json --compact --fields key,name`.
  Default priority: 3 (medium).

Extract from the ticket identifier:
- **Team prefix**: the letters before the dash (e.g., `FAC`).
- **Issue number**: the digits after the dash (e.g., `456`).

## Create Branch

```bash
DEFAULT_BRANCH=$(git remote show origin 2>/dev/null | awk '/HEAD branch/ {print $NF}')
git fetch origin
git checkout -b "ain3sh/<prefix>-<number>-<stub>" "origin/$DEFAULT_BRANCH"
```

- Derive `<stub>` from the ticket title: lowercase, hyphenated, ASCII-only.
- **Full branch name must be <= 32 characters.** Truncate the stub to fit.
- Example: `FAC-456 "Fix onboarding tooltip"` -> `ain3sh/fac-456-fix-onboard`


