---
name: quality-ship
description: Shared atom for running quality checks, committing, and pushing. Background knowledge for workflow commands -- not invoked directly.
user-invocable: false
---

# Quality Checks + Ship

Exact invocations, monorepo/test scoping tables, and known dead ends live in
`references/validator-recipes.md` -- load it before running slop-scan,
react-doctor, or anything in a monorepo. This file owns policy: what runs,
what blocks, what gets logged.

## Pre-check: worktree environment

```bash
MAIN_REPO=$(git worktree list | head -1 | awk '{print $1}')
[ "$(git rev-parse --show-toplevel)" != "$MAIN_REPO" ] && echo "WORKTREE"
```

If in a worktree, follow the **worktree-setup** skill before any checks.
Never `npm install` or `pip install` in a worktree.

## Capture check output file-first

Every check invocation tees full output to a log BEFORE any filter:

```bash
npx vitest run <paths> 2>&1 | tee /tmp/qs-test.log | tail -n 30
```

- Summaries print last, so `tail` after the tee answers pass/fail in one observation; the log keeps everything.
- To see different output, query the log (`rg`, Read) -- **never re-run a check just to change the filter**. Re-running to re-filter is the defect.
- `$?` after a pipeline is the last filter's exit code, not the check's, and `| head` closing the pipe early can SIGPIPE-kill the runner. Read pass/fail from the log, or `set -o pipefail` first (bash/zsh).
- The `capture` hook enforces this: recognized validator commands that filter without capturing get the tee'd re-run command handed to them (interactively as a deny; in `droid exec` as a post-run note), and captured runs get pointed at their log. That log is the evidence of record. Rationale, per-runner shapes, and the config-owned tools list: `references/validator-recipes.md`.

## Run all detected checks

Detect tooling from root and affected-workspace configs and package scripts,
then run each applicable check:

| Check | Detection signals | Typical command |
|-------|-------------------|-----------------|
| Format | `.oxfmtrc*`, `.prettierrc*`, `biome.json*`, `dprint.json*`, configured package scripts | `oxfmt --write --threads=1 <paths>` / `npx prettier --write <paths>` / `biome format --write <paths>` / `dprint fmt <paths>` |
| Lint fix | `.oxlintrc*`, `eslint.config*`, `.eslintrc*`, `biome.json*`, configured package scripts | `oxlint --fix --threads=1 <paths>` / `npx eslint --fix <paths>` / `biome lint --apply <paths>` |
| Docs lint | changed Markdown + `.markdownlint*`, `markdownlint-cli2` config/script/workflow, `remark` config/script | configured script / `markdownlint-cli2 <paths>` / `remark <paths>` |
| Docs links | changed docs + `lychee.toml`, `.lycheeignore`, Lychee script/workflow/action | configured script / `lychee <configured-args> <paths>` |
| Dead code (JS/TS) | `knip.*`, `knip` in package.json scripts | `npx knip --workspace <pkg>` (monorepo) / `npx knip` |
| Dead code (Python) | `*.py` in diff + `pyproject.toml` / `setup.py` | `vulture <changed-paths>` (or `uvx vulture`) |
| AI-slop (JS/TS) | any `*.{js,jsx,ts,tsx}` in diff | `slop-scan delta` on changed-files temp dirs (recipe in references) |
| React diagnostics | `react`/`react-dom`/`next`/`@remix-run/*` in `package.json` | `react-doctor . --scope changed --base <base> --verbose` |
| Type check | `tsconfig.json` | `npx tsc --noEmit -p <pkg>` |
| Tests | `jest.config*`, `vitest.config*`, `pytest.ini` | Changed-file subset, serial workers (rules below) |

- Every detected engine is a separate signal: Oxlint does not imply ESLint is
  redundant, and Oxfmt does not prove Prettier is absent. Read the package
  scripts and configs to identify the actual owners.
- Prefer a repository's narrow package script when it preserves cwd-sensitive
  config, env, or a deliberate multi-engine sequence. Otherwise invoke the
  tool directly on changed paths.
- **Avoid repo-wide aggregate scripts** (`npm run fix` / `npm run check`):
  they can chain every tool across the monorepo. A package-scoped aggregate is
  valid when the package script is the canonical owner; record the scope and
  reason in the checklist evidence.
- Fix any issues found. Re-run until clean.

## Fix the cause, don't suppress the validator

A failing validator is signal: assume it's right and fix the underlying code -- remove the dead export knip found, narrow the type instead of casting, handle the swallowed error. Silencing it just ships the problem.

Escape hatches (`eslint-disable`/`oxlint-disable`, knip `ignore*`, `@ts-ignore`/`@ts-expect-error`, looser `tsconfig`, `# noqa`/`# type: ignore`/vulture whitelists/`# pragma: no cover`, test skips/`.only`/`xfail`) are last resorts for genuine false positives on a specific line -- scoped as narrowly as possible, with a comment justifying *why* it's safe.

Blocking policy: new slop-scan violations block, always. react-doctor errors block; warnings block for `security`, `correctness`, `state-and-effects`, `server` -- advisory for `design`. If the slop-scan file list is empty, skip it (`no signal`).

## Repo conventions (documented)

Validators cover mechanics; they're blind to the idioms a repo documents in prose (error handling, file organization, test placement, flags) -- the rules reviewers flag once the gate is green. Follow the **repo-conventions** skill: discover, diff-scope, apply, emit the `conventions:` row. `no signal` only when the repo documents none -- not when reading was inconvenient.

## Mandatory gate -- before committing

Emit a checklist covering the worktree pre-check and every table row:

```
quality-ship checklist:
- worktree:  <main | repaired> (evidence)
- format:    <ran | no signal> (evidence)
- lint:      <ran | no signal> (evidence)
- docs-lint: <ran | ci-only | no signal> (evidence)
- docs-links: <ran | ci-only | no signal> (evidence)
- dead-code: <ran | no signal> (evidence)
- ai-slop:   <ran | no signal> (evidence)
- react:     <ran | no signal> (evidence)
- conventions: <applied | no signal> (evidence)
- typecheck: <ran | no signal> (evidence)
- tests:     <ran | no signal> (evidence)
```

`evidence` = command run (+ capture log path when tee'd), workflow/config path
for `ci-only`, or missing config (validators); detection output + `repair.py`
invocation (worktree). Don't commit until every line is filled. When detection
emits `WORKTREE`, `worktree: repaired` is the only valid tag -- not "looks
fine, skipped".

`ci-only` means the repository configures a check only in CI and no local
runner is available without installing or reproducing CI infrastructure.
`no signal` means the tool is **genuinely not configured** in the repo, not
that a convenient scoped script is missing. When the tool exists but no
pre-wired scoped task does, scope it yourself with the tool's own flags
(`oxfmt <paths>`, `oxlint <paths>`, `eslint <paths>`,
`knip --workspace <pkg>`, `tsc -p <pkg>`, `vulture <paths>`) or by `cd`ing
into the package. Skipping it or running it unscoped both ship as `no signal`
lies.

## Scoping rules

1. **Put each flag where its owning process parses it.** npm workspace flags
   go before the script name's `--`; Turbo/test-runner flags passed through an
   npm script go after `--`. Inspect the script before choosing. Per-runner
   dialects and the npm/Turbo trap: references.
2. **A "scoped" check that runs minutes is mis-scoped.** Suspect the flag position or dialect before blaming the repo.
3. **HARD RULE: never run a full test suite to validate a diff.** A bare `npm test` / `run test` / `turbo run test` with no path argument is a defect -- stop and re-scope before it runs. Full-suite runs are CI's job. The one exception -- a genuinely cross-cutting change -- must be logged: `tests: full-suite (reason: <why>)`.
4. **Tests have two scope axes; you need both.** The package filter picks *which suite*; only a changed-file subset narrows *which tests*: positional paths, or Jest `--findRelatedTests <changed src files>`. Derive from `git diff --name-only` vs the base. Serial workers by default (flags in references).
5. This governs how you **run** tests, not how broad the tests you **write** should be -- never let "run narrow" leak into "write narrow" (see **consolidate-test-suites**).

## Commit

```bash
git add -A
git commit -m "<type>(<scope>): <subject> (<TICKET-ID>)" -m "<body>"
```

- Conventional commit format. Type: `fix`, `feat`, `refactor`, `docs`, `chore`, `test`, etc. Subject <=72 chars, imperative ("add", not "added"). Reference the Linear ticket.
- **Body required** unless the change is trivial (typo, formatting, single-name rename). The body explains *why* -- the diff shows *what*. For review-feedback or CI-fix commits, name the threads / failures the body addresses.

## Push

```bash
git push -u origin HEAD
```

## PR Description Refresh

After pushing, check if a PR is already open for the current branch:

```bash
gh pr view --json number --jq '.number' 2>/dev/null
```

If a PR exists, follow the **pr-description** skill's post-push refresh flow (section 6): run the staleness check against the new diff, then the coherence pass only if updates are needed.
