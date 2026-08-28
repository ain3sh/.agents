# dsx command reference

All query commands support `--json` (stable shapes, treated as a public
contract) and auto-refresh the index first; add `--no-refresh` when running
many commands in a row. Session arguments accept 8-char id prefixes. Time
refs: `7d`, `24h`, `30m`, `2026-05-01`.

## find sessions

```bash
dsx list [-q "fuzzy title"] [-p <project>] [--since <when>] [--until <when>]
         [--model <substring>] [--min-credits <n>] [--all]
         [--sort updated|created|tokens|credits|messages|active] [-n 25] [--json]
```

- `-p/--project` matches the session cwd as a substring.
- Subagent and droid-exec sessions are hidden unless `--all`.

## full-text search

```bash
dsx search "<query>" [-p <project>] [--session <id>] [-r user|assistant]
          [--type text,thinking,tool_use,tool_result] [--tool <name>] [--errors]
          [--since <when>] [--until <when>] [-n 25] [--json]
```

- FTS5 syntax: `"exact phrase"`, `AND`, `OR`, `NOT`, `NEAR(a b, 5)`. Invalid
  syntax is auto-quoted, so raw error strings are safe to paste.
- Hits include `sessionId` + `seq` (message ordinal) to locate context within
  a transcript; JSON snippets mark matches with `[` `]`.
- `--errors` restricts to failed tool results; combine with `--tool Execute`.

Two alternate engines share the command:

```bash
dsx search "<regex>" --regex [-i]     # ripgrep over the raw JSONL transcripts
dsx search "<text>" --history         # the user's typed prompt history
```

## inspect a session

```bash
dsx show <id> [--json]                # metadata, usage, tool histogram, final todos
dsx export <id> [--no-tools] [--no-thinking] [-f md|html] [-o <file>]
dsx path <id> [--transcript] [--all] [--json] # JSONL= and SETTINGS= file paths
dsx tree <id> [--json]                # fork + subagent lineage
dsx resume <id> [--run]               # print (or exec) `cd ... && droid --resume <id>`
```

The exporter reads source JSONL, so content is full-fidelity even though the
index caps indexed block size.

`dsx path <id> --all` bypasses the index and scans the sessions root on disk,
grouping every match into complete pairs, transcript-only, and settings-only
files. Use it to debug orphans or duplicate ids the index can't represent (it
accepts an id prefix and never fails on a miss). JSON shape:
`{ ref, root, pairs:[{id,transcript,settings}], transcriptOnly:[{id,transcript}],
settingsOnly:[{id,settings}] }`.

## analytics

```bash
dsx stats [--by day|model|project|tool|hour|day-model|day-project|
              project-model|day-tool|project-tool|model-tool|segment|dist]
          [-p <project>] [--model <substring>] [--since <when>]
          [--until <when>] [--metric <metric>] [--all] [--json]
dsx insights [-p <project>] [--since <when>] [--kind <kind>] [-n 20] [--json]
dsx insights --deep [-m <model>] [--reasoning low|medium|high] [--json]
dsx ask "<question>" [-m <model>] [--cwd <path>]
```

- `insights` semantics (kinds, severity, outlier math) are documented in
  `insights.md`.
- Usage scope and fork-inflation caveats are documented in
  `usage-semantics.md`; stats cross-tab semantics are in `stats-analytics.md`.
- `stats` excludes subagent and droid-exec sessions by default; add `--all`
  to include them. `--by segment` always shows `main`, `subagent`, and `exec`
  buckets so you can see what `--all` changes.
- Cross-tabs:
  - `day-model` / `day-project`: daily usage split by model or project.
  - `project-model`: model mix inside each project.
  - `day-tool` / `project-tool` / `model-tool`: tool calls and error rates by
    the chosen dimension.
  - `dist`: percentiles and histogram for `credits`, `tokens`/`totalTokens`,
    `active`, or `toolErrors`.
- Chart-oriented views honor `--metric`; common metrics include `credits`,
  `inputTokens`, `outputTokens`, `totalTokens`, `messages`, `sessions`,
  `toolCalls`, `toolErrors`, `errorRate`, and `tokensPerMessage`.
- `--deep` spawns a droid exec sub-agent that mines the index and writes a
  cited brief; the result streams to stdout and is cached for the TUI.
  Defaults come from `$DSX_INSIGHTS_MODEL` (kimi-k2.6) and
  `$DSX_INSIGHTS_REASONING` (low).
- `ask` delegates a one-off question to a sub-droid with this reference in its
  prompt.

## papercuts

```bash
dsx papercut add "<concrete friction>" [--session <id>] [--json]
dsx papercut list [-p <project>] [--session <id>] [--source manual|review]
                  [-n 25] [--json]
dsx papercut review <id> [-m <model>] [--reasoning low|medium|high]
                         [--save] [--json]
```

- `add` records one manual papercut and attributes it to a recently active
  session in the current cwd when possible; use `--session` for exact
  attribution.
- `review` sends one transcript to a low-reasoning droid exec run, removes
  exact duplicates, and previews candidates. It writes only with `--save`.
  Its default model is `$DSX_PAPERCUT_MODEL` or `gpt-5.6-luna`.
- Records are append-only JSONL at
  `$XDG_DATA_HOME/dsx/papercuts.jsonl`; `$DSX_PAPERCUTS_PATH` overrides the
  path. This is durable source data and survives index rebuilds.
- JSON shapes:
  - `add`: `PapercutRecord`
  - `list`: `PapercutRecord[]`
  - `review`: `{sessionId, model, reasoningEffort, candidates:[{message}],
    saved:PapercutRecord[], execSessionId}`; `saved` is empty without `--save`
  - `PapercutRecord`: `{id, createdAt, message, source, cwd, project,
    sessionId:string|null, model:string|null}`

## maintenance

```bash
dsx index [--rebuild] [--json]                  # force refresh / full re-ingest
dsx migrate-path <oldPrefix> <newPrefix> [--apply]  # after moving a project dir
         [--cwd-only] [--dirs-only] [--rename-conflicts]
         [--backup-dir <dir>] [--root <dir>]
dsx skill sync [--to <dir...>] [--apply]    # (re)install this skill; --apply reuses saved choice
```

- `migrate-path` is a dry run unless `--apply` (which backs up first). `--root`
  overrides the session root it operates on (otherwise the configured root /
  `DROID_SESSION_ROOT`); `--cwd-only`/`--dirs-only` scope the rewrite to JSONL
  `cwd` fields or encoded session dirs respectively.
