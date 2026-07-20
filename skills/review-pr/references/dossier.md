# Review dossier

The compact, durable record of a review — what was found, what was proven safe, and what was covered. Follow-up loads this instead of replaying a giant transcript or re-deriving state from GitHub threads. Killed suspicions are as valuable as findings: they are what stops the next pass from re-investigating settled ground.

## Location

```text
./.agents/review.md        (review-worktree root)
```

Reviews run in a dedicated worktree per PR, so the worktree is the namespace — one dossier per worktree, **replaced** (not appended) each pass, with a one-line history log per pass at the bottom. `mkdir -p ./.agents` on first write. The file is untracked and stays that way: never commit it; workers never touch it (main reviewer owns it).

On load, verify the dossier's PR number matches the target — mismatch (e.g. review run from a shared worktree) → treat as no dossier. Worktree deleted → dossier gone; that's fine — the GitHub review thread is the durable signal, and follow-up reconstructs the minimum from it.

## Lifecycle

- **Write** after every posted review (first-pass, post-overcoverage, follow-up) — `/post-review` owns the write as its final step after submitting.
- **Load** at the start of every follow-up, and to answer "did we already review this?" during routing.
- **Replace** reviewed-head, findings, verified-safe, and coverage sections with current state each pass; append one line to the history log.

## Schema

```markdown
# PR <number> — <title>

repo: <owner>/<repo>
reviewed_head: <SHA>
base: <base ref> @ <merge-base SHA>
mode: <first-pass | first-pass+deeper | follow-up>
verdict: <APPROVE | COMMENT>
date: <ISO date>

## Root-cause / invariant model
<2-6 lines: what the PR claims to establish, the layer it lives in,
and whether the review confirmed that model.>

## Findings (as posted)
- <severity> <file:line> — <claim> — <evidence, one line> — thread: <GitHub comment URL or id> — status: <open>

## Verified safe
- <suspicion> — killed by <invariant | probe result>, <one-line evidence>

## Coverage map
- <surface>: <main | static worker | probe worker> — <outcome>
- <surface>: not deeply covered — risk <low | medium | high>

## Unresolved
- <question left open at post time, if any>

## Worker log
- <category>: <static sid?, heavy sid?> — <conclusion, incl. cancellations and why>

## History
- <date> first-pass @ <SHA>: <verdict>, <n> findings
- <date> follow-up @ <SHA>: <verdict>, <resolved x/y, new z>
```

Keep it under ~100 lines. Evidence is one-line summaries with pointers (thread URLs, session ids) — not transcripts. If a section is empty, keep the header with "none"; follow-up relies on the distinction between "none" and "not recorded".
