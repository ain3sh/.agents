# Usage semantics

Rules for reading cost and usage totals correctly.

## Fork chains inflate per-session totals

Forked sessions inherit the parent's cumulative token/credit usage at fork
time, so every `[Fork]` session reports its whole lineage's spend, not its own
increment. Consequences:

- Never sum credits across a fork chain; that double-counts. A linear chain's
  true total is roughly the deepest fork's figure alone.
- Before attributing cost to a session titled `[Fork] ...`, run
  `dsx tree <id>` and reason about the lineage root.
- Expect fork-heavy projects to dominate any naive "most expensive sessions"
  ranking.

## What is excluded, and from where

- Subagent and droid-exec sessions are excluded from `dsx stats` and
  `dsx insights`, and hidden from `dsx list` unless `--all`.
- `dsx stats --by segment` is the exception: it always reports `main`,
  `subagent`, and `exec` buckets so you can see how much spend/activity the
  default scope excludes.
- dsx's own LLM features (`dsx ask`, `dsx insights --deep`) run as droid exec
  sessions tagged `exec` + `dsx-insights`, so they never pollute their own
  reports.
