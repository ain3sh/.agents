---
name: dsx
description: Search and analyze past Factory Droid sessions with the dsx CLI. Use for previous work, session history, usage analysis, or proactively after two failed attempts at the same tooling, environment, deployment, or operational problem that may have been solved before.
---

# dsx: Droid Session Explorer

`dsx` indexes every local droid session (`~/.factory/sessions`) into a fast
SQLite+FTS5 index: full transcripts, token usage, tool calls, fork/subagent
lineage, and the user's prompt history. The index auto-refreshes before every
command (sub-second); add `--no-refresh` when running many commands in a row.

Every query command supports `--json` with stable shapes. Prefer it.

## When this fires & how to load it

This entrypoint is enough for simple lookups. Load a reference when its
trigger fires:

| Read | When |
|---|---|
| `references/commands.md` | composing non-trivial queries: full flag surface, FTS5 syntax, JSON hit shapes, export/maintenance commands |
| `references/usage-semantics.md` | reasoning about costs, tokens, fork inflation, subagents, or droid-exec exclusion |
| `references/stats-analytics.md` | reasoning about `dsx stats` cross-tabs, pro-rating, metrics, or distributions |
| `references/insights.md` | reasoning about `dsx insights` signal kinds, severity, and report-level rates |

## Core workflow

**Recovery trigger:** after two failed attempts at the same operational or
tooling problem, stop inventing new hypotheses and search history before a
third. Query the exact error or distinctive symptom in the current project,
then inspect the best prior session for the proven fix.

1. Start broad: `dsx search "<query>" --json` or `dsx list --json` with filters.
2. Drill in: `dsx show <id>` for the shape, `dsx export <id> --no-tools` for content.
3. Cite session ids (8-char prefixes are fine) for every claim about past work.
4. Costs and usage: `dsx stats --by model|project|day|day-model|day-project --since 30d`. Before
   attributing cost, read `references/usage-semantics.md` (fork chains
   inherit cumulative usage; naive sums double-count).
5. "What went wrong lately": `dsx insights --since 30d`.
6. Record small workflow friction in the moment with `dsx papercut add`.

## Quick reference

```bash
dsx list -q "auth refactor" --project vfs --since 7d --sort credits --json
dsx search "race condition" --type thinking --json     # FTS5 over transcripts
dsx search "cache.*miss" --regex --json                # ripgrep over raw JSONL
dsx search "refactor" --history --json                 # user's typed prompts
dsx show 22bc0eed --json                               # summary, usage, tool stats
dsx path 22bc0eed                                      # JSONL= / SETTINGS= paths (add --all to scan disk for orphans)
dsx export 22bc0eed --no-tools                         # markdown transcript
dsx tree 22bc0eed                                      # fork + subagent lineage
dsx resume 22bc0eed                                    # prints the resume command
dsx stats --by model --since 30d --json
dsx stats --by day-model --metric totalTokens --since 30d --json
dsx stats --by day-tool --since 7d
dsx insights --since 30d --json                        # heuristic findings
dsx insights --deep                                    # LLM-written usage brief
dsx ask "when did I last touch the auth flow?"         # delegate to a sub-droid
dsx papercut add "The test cwd made the path miss."     # durable manual record
dsx papercut list --project demo --json                 # query recorded friction
dsx papercut review 22bc0eed                            # preview transcript findings
dsx papercut review 22bc0eed --save                     # append reviewed findings
```

Subagent and droid-exec sessions are hidden from `dsx list` and excluded from
`dsx stats` by default; add `--all` to include them.

Papercuts are durable source data at
`$XDG_DATA_HOME/dsx/papercuts.jsonl` (override with
`$DSX_PAPERCUTS_PATH`), not part of the rebuildable session index. Transcript
review is explicit and preview-only unless `--save` is passed.
