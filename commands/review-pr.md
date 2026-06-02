---
description: Review a PR -- typed verification + shared criteria, surface findings for approval; /post-review publishes.
argument-hint: <PR-number-or-URL>
---

Load skills: **pr-context**, **linear-cli**, **worktree-setup**, **quality-ship**, **review-voice**, **repo-conventions**.

**Targeted scope = the PR's changed files** (`gh pr diff <PR> --name-only`, or via **pr-context**). Reviewer's job is judgment (architecture, root cause, broader impact, convention adherence, slop), not re-running what PR CI already covers. When a step below needs setup or a validator (repro in §3, slop-scan in §4), use **worktree-setup**'s `repair.py` (never `verify.py` — its full-workspace manifest demands out-of-scope artifacts) and **quality-ship**'s validator patterns; don't wing it — that derails focus.

**Workers in flight.** If a subagent is still making progress (output / tool calls visible), **let it finish**. Don't `TaskStop` over resource-usage or token-budget worries — review quality outranks both. Stop only if genuinely stalled or off-task.

**Worker complexity.** Any `Task` dispatched from this flow — coverage sweeps, slop scans, repro runs, per-area reviewers — **must** pass `complexity: "heavy"`. The default `medium` is too weak for review judgment (root-cause tracing, architecture critique, slop discrimination) and produces shallow findings. Don't omit `complexity` or downgrade to save tokens. If a sweep is genuinely trivial (one-file typo PR), do it inline rather than dispatching.

## 1. Gather context

Follow **pr-context** to fetch metadata, conversation, diff, and linked Linear ticket; derive `REPO` and `HEAD_SHA` from `$ARGUMENTS`.

## 2. Classify PR type

Infer from title prefix, labels, ticket, and changed files:

| Type | Signals |
|------|---------|
| **Bug fix** | title `fix(...)`, label `bug`, ticket describes broken behavior |
| **Feature** | title `feat(...)`, label `feature`/`enhancement`, ticket describes new capability |
| **Refactor/chore** | title `refactor`/`chore`/`perf`/`docs`, no user-facing behavior change |
| **CI/Infra** | title `ci`/`build`, changes only in `.github/`, `infra/`, config files, scripts |

If ambiguous, default to **Feature**.

## 3. Type-specific verification

### Bug fix

**Mandatory repro before code review** -- catches fixes that mask symptoms without addressing root cause.

1. Checkout base. Repair (`repair.py`) if cwd is a worktree. Run **only** the ticket's minimal repro command — no broad install/build/validate cycle. Confirm failure.
2. Checkout PR branch. Repair if needed. Re-run the same command. Confirm fix.
3. Code-review with a **root-cause lens**: actual cause, or papering over a symptom? Right layer?

### Feature

1. Check against the ticket's acceptance criteria; flag gaps.
2. Evaluate API/UX design -- consistent with existing patterns? Will it age well?

### Refactor/chore

1. Verify **behavior preservation** -- no functional change unless explicitly stated.
2. Check for incomplete migration: missed renames, stale references, orphaned code.

### CI/Infra

1. Pipeline correctness and idempotency (safe to re-run?).
2. Secret handling, permissions scope, exposed surfaces.
3. Loosen code-style scrutiny on YAML/shell.

## 4. Shared review criteria

See **review-voice** for criteria, severity taxonomy (`critical|warning|opinion|suggestion|nit`), and the mandatory unprompted-opinion sweep.

Plus the repo's **own documented conventions** -- hold the author to the same standard we hold ourselves. Follow the **repo-conventions** skill (discover + diff-scope against the PR's changed files, then read the selected docs) and reconcile the diff against them. Here you **flag, not fix**: fold each deviation into findings at `warning` (a clear written rule -- error handling, file organization, test placement, flags -- broken) or `suggestion` (softer guidance). A repo-provided pre-PR checklist is itself review criteria -- check the diff against each item.

Plus the **AI-slop validator** (JS/TS only):

```bash
BASE_REF=$(gh pr view <PR> --json baseRefName --jq '.baseRefName')
git fetch origin "$BASE_REF"
BASE_SHA=$(git merge-base "origin/$BASE_REF" "$HEAD_SHA")
BASE_WT=$(mktemp -d); HEAD_WT=$(mktemp -d)
git worktree add --detach "$BASE_WT" "$BASE_SHA"
git worktree add --detach "$HEAD_WT" "$HEAD_SHA"
slop-scan delta "$BASE_WT" "$HEAD_WT" --json
git worktree remove --force "$BASE_WT" && git worktree remove --force "$HEAD_WT"
```

Detached source snapshots — slop-scan reads source, not built artifacts. **Don't repair/verify.** Install if missing: `npm install -g slop-scan`; otherwise skip.

Hits (swallowed errors, placeholder comments, generic casts, pass-through wrappers, duplicate signatures, …) fold into findings at `warning` (likely to fire / hides real failure) or `opinion` (structural smell).

## 5. User approval gate

Show every finding to the user before posting:

- Group by file; include severity, line, suggested fix.
- State intended verdict (`APPROVE` / `COMMENT`).
- Plain chat prose; **do not use `AskUser`** -- the user should be free to discuss, reword, drop, or re-severity findings.
- **Wait for explicit confirmation.** Apply any user edits before handoff.

Once confirmed, hand off to `/post-review <PR-number-or-URL>`. Suggestion-block decisions live there -- review judgment must not be biased toward apply-clickable issues.
