---
name: notion-cli
description: Reference for using ntn (Notion CLI) to manage Notion pages, data sources, workers, and raw Notion API requests from the terminal. Use when the user mentions Notion pages, databases, workers, or syncs.
---

# Notion CLI (`ntn`)

OAuth into the OS keychain, workspace-scoped. For CI, export `NOTION_API_TOKEN=ntn_…` (PAT) — it overrides the keychain.

## Authentication

```bash
ntn login                                          # Browser OAuth → keychain (rerun to switch workspace)
ntn login poll                                     # Headless: complete after browser auth on another device
ntn logout                                         # Clear all workspace credentials
ntn doctor                                         # Auth/keychain/network/config; shows workspace IDs
ntn update                                         # Self-update (--force reinstalls)
```

One-shot a non-default workspace: `NOTION_WORKSPACE_ID=<id> ntn …`.
No-keychain hosts (Docker, CI, headless SSH): `NOTION_KEYRING=0 ntn login` writes plain JSON to `auth.json`.

## Pages

```bash
ntn pages get <page-id>                            # → Markdown
ntn pages get <page-id> --json                     # → raw blocks JSON
ntn pages create --parent page:<id> --content "# Title"
ntn pages create --parent database:<id> < page.md  # Body from file
ntn pages create --parent data-source:<ds-id>      # No --content → reads stdin
ntn pages update <page-id> --content "new md"
ntn pages update <page-id> --allow-deleting-content # Permits removing child pages/dbs
ntn pages trash <page-id> --yes
```

`--parent` shape: `page:<id>` | `database:<id>` | `data-source:<id>`. All page commands accept `--notion-version <ver>` (or `NOTION_API_VERSION`).

## Data sources

Notion databases hold one or more *data sources*; query operations target a DS, not the DB.

```bash
ntn datasources resolve <db-id>                    # DB id → DS id(s)
ntn datasources query <ds-id>                      # First page (default 25)
ntn datasources query <ds-id> --limit 100 --start-cursor <c>
ntn datasources query <ds-id> -s "Name asc" -s "Priority desc"
ntn datasources query <ds-id> --filter '<json>'    # Or --filter-file f.json | --filter-file -
```

Filter shape: see Notion API "Filter data source entries".

## Files

```bash
ntn files create                                   # Upload
ntn files list
ntn files get <upload-id>
```

## Raw Notion API (`ntn api`)

Injects `Authorization` + `Notion-Version`. No body → `GET`; any body input → `POST` unless `-X` overrides.

```bash
ntn api v1/users/me                                # Leading slash optional
ntn api ls [--json]                                # All endpoints
ntn api v1/comments --help                         # Live endpoint help
ntn api v1/comments --spec -X POST                 # Reduced OpenAPI (pass -X for multi-method paths)
ntn api v1/comments --docs -X POST                 # Markdown reference page
ntn api v1/users/me --notion-version 2026-03-11    # Pin version
ntn --verbose api …                                # Trace method/URL/headers/body/status/x-request-id
```

`--verbose` redacts `Authorization`. `--unsafe-verbose` disables redaction — never paste its output anywhere shared.

### Inline request DSL

| Form | Meaning | Example |
|------|---------|---------|
| `path=value` | Body field, string | `parent[page_id]=abc123` |
| `path:=json` | Body field, parsed JSON | `archived:=true` |
| `name==value` | Query parameter | `page_size==100` |
| `Header:Value` | Request header | `Accept:application/json` |

Use `=` for strings, `:=` for booleans/numbers/`null`/arrays/objects. Bracket notation handles keys with spaces or punctuation; `[]` appends, `[N]` sets explicit indexes; bracket and dot syntax both nest.

```bash
ntn api v1/pages \
  parent[page_id]="$PARENT" \
  properties.Name.title[0].text.content="Meeting notes"

ntn api "v1/pages/$ID" -X PATCH archived:=false properties[Priority][number]:=2

ntn api "v1/blocks/$ID/children" -X PATCH \
  children[0][type]=heading_2 \
  children[0][heading_2][rich_text][0][text][content]="Section header"
```

### Body sources (pick one)

```bash
ntn api v1/pages < create-page.json                # Stdin
jq -n '...' | ntn api v1/pages                     # Pipe
ntn api v1/search --data '{"query":"roadmap"}'     # Direct JSON
ntn api v1/pages parent[page_id]=…                 # Inline DSL
```

Stdin / `--data` / inline-DSL are mutually exclusive. Headers and `==` query params combine with any one.

## Workers

Workers package syncs / tools / webhooks. Worker resolution: `--worker-id` → positional `<worker-id>` → `workerId` in `./workers.json`. Most subcommands accept `--json` (or `--plain` for TSV). Aliases throughout: `list`↔`ls`, `delete`↔`rm`, `tui`↔`ui`.

```bash
ntn workers new [dir]                              # Scaffold (--git/--no-git, --install/--no-install, --force)
ntn workers deploy                                 # Build + upload (creates if no workers.json)
ntn workers deploy --name <n>                      # Required on first create; forbidden on update
ntn workers deploy --local-build                   # Build locally, skip cloud build
ntn workers deploy --no-git                        # Walk filesystem instead of git
ntn workers list
ntn workers get [worker-id]
ntn workers create --name <n>                      # Empty worker, no code deploy
ntn workers delete [worker-id] --yes
ntn workers tui                                    # Interactive UI
ntn workers capabilities list                      # Deployed capabilities

ntn workers exec <key>                             # Run capability; reads stdin
ntn workers exec <key> -d '{"x":1}'                # Inline JSON input
ntn workers exec <key> --stream                    # Stream output as produced
ntn workers exec <key> -l                          # Run locally via tsx
ntn workers exec <key> -l --dotenv .env.local      # Custom env file (default .env, --no-dotenv to skip)
```

### Syncs (scheduled capabilities)

```bash
ntn workers sync status [<key>]                    # Live; --no-watch (once), --interval 5 (default 2s)
ntn workers sync trigger <key>                     # Run now, bypass schedule
ntn workers sync trigger <key> --preview           # Dry run, no writes
ntn workers sync trigger <key> --context '<json>'  # Resume from prior --preview nextContext
ntn workers sync trigger <key> -l                  # Local via tsx (--dotenv / --no-dotenv apply)
ntn workers sync pause <key>                       # Halt schedule (in-flight runs continue)
ntn workers sync resume <key>
ntn workers sync state get <key>                   # Cursor + stats
ntn workers sync state reset <key>                 # Restart on next run
```

### Env vars (encrypted, write-only)

```bash
ntn workers env set FOO=bar BAZ=qux                # One or many
ntn workers env list                               # Keys only — values never returned
ntn workers env unset FOO                          # Aliases: delete, rm
ntn workers env pull                               # → ./.env (--file <path> | --no-file for stdout)
ntn workers env push                               # ← ./.env (--file <path>, --yes to skip confirm)
```

### OAuth, runs, webhooks

```bash
ntn workers oauth start <key>                      # Open provider authorize URL
ntn workers oauth token <key>                      # Print access token (debug); --plain for bare token
ntn workers oauth show-redirect-url                # URL to register with the provider
ntn workers runs list                              # Recent runs
ntn workers runs logs <run-id>
ntn workers webhooks list [worker-id]              # Webhook URLs
```

## Flags & Environment

| Flag | Description |
|------|-------------|
| `-v, --verbose` | Full error chains; on `api`, dumps request/response |
| `--workers-config-file <p>` | Override `workers.json` lookup; its `workspaceId` selects workspace |
| `-V, --version` / `-h, --help` | Standard |

| Variable | Purpose |
|----------|---------|
| `NOTION_API_TOKEN` | PAT; takes precedence over the keychain |
| `NOTION_WORKSPACE_ID` | One-shot workspace selector |
| `NOTION_KEYRING` | `0` → file-based auth at `auth.json` |
| `NOTION_API_VERSION` | Default `Notion-Version` for `api` |
| `NOTION_WORKERS_CONFIG_FILE` | Same as `--workers-config-file` |
| `NOTION_HOME` | Override config dir (`$XDG_CONFIG_HOME/notion`) |

Shell completions: `ntn completions {bash|zsh|fish|powershell|elvish}`.

## Patterns

### Page id from a URL

URL shape: `https://www.notion.so/<workspace>/<slug>-<32-hex>?…`. Strip everything but the trailing 32 hex chars:

```bash
PAGE_ID=$(echo "$URL" | grep -oE '[0-9a-f]{32}' | tail -n1)
ntn pages get "$PAGE_ID"
```

### Database → page rows

`datasources` operate on data source IDs, not database IDs:

```bash
DS_ID=$(ntn datasources resolve "$DB_ID" --json | jq -r '.[0].id')
ntn datasources query "$DS_ID" --limit 100 --filter-file ./filter.json
```

### Capture x-request-id for support

```bash
ntn --verbose api "v1/pages/$ID" -X PATCH archived:=true 2>&1 | tee /tmp/ntn-trace
grep -i 'x-request-id' /tmp/ntn-trace
```

## Known Limitations

- `ntn login` rejects guests and restricted members — admin must upgrade your role, or use a PAT.
- `workers env push` reads `./.env` by default — confirm `--file` before pushing against production secrets.
- Headless `ntn login` sessions expire quickly; restart `ntn login` if `poll` fails.
