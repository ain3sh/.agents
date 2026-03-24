---
description: Create a new Linear ticket
argument-hint: <title> [-t TEAM] [-p priority]
---

## Steps

1. If `$ARGUMENTS` provides a title and details, use them. Otherwise ask for:
   - Title (concise, action-oriented)
   - Team (discover with `linear t list --output json --compact --fields key,name`)
   - Priority (1=urgent, 2=high, 3=medium, 4=low; default 3)
   - Description (optional)
   - Labels (optional; discover with `linear l list --output json --compact --fields name`)
2. Create: `linear i create "<title>" -t <TEAM> -p <priority>`
   - If description provided: pipe via stdin or use `-d "<desc>"`
   - If labels provided: add `-l <label>` for each
   - Append `--id-only --quiet` when chaining into other workflows.
3. Report the ticket identifier and URL via `linear i link <ID>`.
