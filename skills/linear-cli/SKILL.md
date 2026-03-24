---
name: linear-cli
description: Reference for using linear-cli (aliased as `linear`) to manage Linear.app issues, projects, cycles, and sprints from the terminal. Use when the user mentions Linear tickets, issues, project management, or sprint planning.
---

# Linear CLI (`linear`)

linear-cli is authenticated via OAuth 2.0. Verify with `linear doctor`.

## Issues

```bash
linear i list --mine                              # My issues
linear i list -t TEAM --mine                      # Scoped to team
linear i list --since 7d --group-by state          # Grouped
linear i list --label bug --count-only             # Count

linear i get TEAM-123                              # Details
linear i get TEAM-123 --comments                   # With comments
linear i get TEAM-1 TEAM-2 TEAM-3                 # Batch

linear i create "Title" -t TEAM -p 1               # Create (1=urgent,2=high,3=med,4=low)
linear i create "Title" -t TEAM -d -               # Pipe description from stdin

linear i update TEAM-123 -s "In Progress"          # Status
linear i update TEAM-123 -l bug -l urgent          # Labels
linear i update TEAM-123 --due tomorrow            # Due date
linear i update TEAM-123 -e 3                      # Estimate

linear i start TEAM-123 --checkout                 # Start + git branch
linear i stop TEAM-123                             # Back to backlog
linear i close TEAM-123                            # Done
linear i assign TEAM-123 "Name"                    # Assign
linear i move TEAM-123 "Project"                   # Move to project
linear i transfer TEAM-123 TEAM                    # Transfer team
linear i comment TEAM-123 -b "text"                # Comment
linear i archive TEAM-123                          # Archive
linear i open TEAM-123                             # Open in browser
linear i link TEAM-123                             # Print URL
```

## Projects & Teams

```bash
linear p list                                      # Projects
linear p get "Name"                                # Details
linear p create "Name" -t TEAM                     # Create
linear t list                                      # Teams
linear t get TEAM_KEY                              # Team details
linear t members TEAM_KEY                          # Members
```

## Cycles & Sprints

```bash
linear c list -t TEAM                              # Cycles
linear c current -t TEAM                           # Current cycle
linear sp status -t TEAM                           # Sprint status
linear sp progress -t TEAM                         # Progress bar
linear sp burndown -t TEAM                         # Burndown chart
linear sp velocity -t TEAM                         # Velocity
```

## Agent Output Patterns

Use these flags when consuming output programmatically:

| Flag | Purpose |
|------|---------|
| `--output json` | JSON (also `ndjson`) |
| `--compact` | No pretty-print |
| `--fields a,b,c` | Limit fields (dot paths) |
| `--id-only` | Only resource ID |
| `--quiet` | Suppress decoration |
| `--format "{{identifier}} {{title}}"` | Template |
| `--filter "state.name=In Progress"` | Client-side filter |
| `--fail-on-empty` | Non-zero exit on empty |
| `--dry-run` | Preview |

### Chaining

```bash
ID=$(linear i create "Title" -t TEAM --id-only --quiet)
linear i update "$ID" -s "In Progress"
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Not found |
| 3 | Auth error |
| 4 | Rate limited |

## Documents, Labels, Templates

```bash
linear d list                                      # Documents
linear d create "Name" -c "Content"                # Create doc
linear l list                                      # Labels
linear l create "name" -c "#FF0000"                # Create label
linear templates list                              # Templates
linear views list                                  # Custom views
```

## Search

```bash
linear search "query"                              # Search issues
linear search "query" --output json --compact      # JSON output
```

## Raw GraphQL API

```bash
linear api query '{ viewer { id name } }'          # Query
echo '{"query":"..."}' | linear api query -         # Pipe
linear api mutate '<mutation>'                      # Mutate
```

## Watch Mode

```bash
linear watch TEAM-123                              # Watch issue changes
linear watch -t TEAM                               # Watch team activity
```

## Import / Export

```bash
linear export -t TEAM --format csv                 # Export CSV
linear export -t TEAM --format json                # Export JSON
linear import --file data.csv -t TEAM              # Import CSV
```
