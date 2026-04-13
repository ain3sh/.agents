# Agent CLI Patterns

Use this reference when designing the command surface for a new CLI.

## Mental model

The CLI turns a service, app, API, log source, or database into shell commands that can be run repeatedly from any repo. Expose composable primitives -- avoid a single command that tries to "do the whole investigation" when smaller discover, read, resolve, download, inspect, draft, and upload commands compose better.

## Help is interface

Write `--help` for a future session that only has the binary and a vague task. Each command should have a short description and flags with literal names from the product or API.

Good top-level help answers:
- What containers can I discover?
- What exact objects can I read?
- What stable IDs can I resolve?
- What files can I download or upload?
- Which write actions exist?
- What is the raw escape hatch?

## Prefer this command shape

Use product nouns, then verbs:

```
tool-name --json doctor
tool-name --json accounts list
tool-name --json projects list
tool-name --json channels resolve --name codex
tool-name --json messages search "exact phrase"
tool-name --json messages context <message-id> --before 3 --after 3
tool-name --json logs download <build-url> --failed --out ./logs
tool-name --json media upload --file ./image.png
tool-name --json drafts create --body-file draft.json
```

The important rule is consistency. Do not mix many styles.

## Useful shapes from mature CLIs

```
# Field-selected structured output
tool-name issues list --json number,title,url,state
tool-name issues list --json number,title --jq '.[] | select(.state == "open")'

# Human text by default, full API object when requested
tool-name pods get <name>
tool-name pods get <name> -o json

# Product workflow commands, not just REST nouns
tool-name logs tail
tool-name webhooks listen --forward-to localhost:4242/webhooks
```

## Discovery, resolve, read, context

Design first-pass commands in this order:

1. **Discover** broad containers: workspaces, accounts, repos, projects, channels, queues.
2. **Resolve** human input into IDs: user names, channel names, permalinks, PR URLs, build URLs.
3. **Read** an exact object: issue, event, thread, draft, customer, job, run, media item.
4. **Context** around an anchor when useful: nearby messages, parent thread, surrounding logs, audit history.

## Text, JSON, files, exit codes

- Emit JSON to stdout only under `--json`. Progress and diagnostics go to stderr.
- Redact tokens, cookies, customer secrets, private headers, and unrelated payloads.
- For downloads: write files under `--out`, return file path and byte count in JSON output.
- Exit zero on success (including empty results). Nonzero for auth failure, invalid input, network failure, API error.
- Make `doctor --json` usable even when auth is missing.

## Pagination and breadth

Start shallow by default:

```
tool-name --json messages search "topic" --limit 10
tool-name --json messages search "topic" --limit 50 --all-pages --max-pages 3
tool-name --json drafts list --limit 20 --offset 40
```

Return `next_cursor`, `next_url`, `offset`, or `page_count` as appropriate.

## Raw escape hatch

The raw command is a repair hatch, not the main interface. It should still use configured auth, base URL, JSON parsing, redaction, and `--json`.

```
tool-name --json request get /v2/me
```

Treat raw writes as live writes.

## Companion skill pattern

The companion skill should teach the path through the tool:

```
Start with:
  tool-name --json doctor
  tool-name --json accounts list

For [common job]:
  tool-name --json ...
  tool-name --json ...

Rules:
- Prefer installed tool-name on PATH.
- Use --json when analyzing output.
- Create drafts by default.
- Do not publish/delete/retry/submit unless the user asked.
- Use request get ... only when high-level commands are missing.
```
