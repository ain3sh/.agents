---
name: quality-ship
description: Shared atom for running quality checks, committing, and pushing. Background knowledge for workflow commands -- not invoked directly.
user-invocable: false
---

# Quality Checks + Ship

Run each scoped check once, attached, with every byte visible live and logged.
Exact invocations, monorepo/test scoping tables, and known dead ends live in
`references/validator-recipes.md` -- load it before running slop-scan,
react-doctor, or anything in a monorepo.

## Act: run checks through one primitive

```bash
~/.agents/scripts/run-check <label> [--cwd <dir>] [--env KEY=VALUE]... -- <scoped-validator-argv>
```

Examples:

```bash
~/.agents/scripts/run-check test -- npx vitest run src/foo.test.ts
~/.agents/scripts/run-check lint -- npx eslint src/foo.ts
~/.agents/scripts/run-check e2e --cwd apps/cli -- npm run test:e2e:run -- e2e-tests/chat-input.test.ts
~/.agents/scripts/run-check custom --env PATH="$HOME/.local/bin:$PATH" -- custom-validator src/foo.ts
```

`run-check` streams complete merged stdout/stderr to the attached Execute
call, writes the same bytes under `/tmp/droid-checks/`, waits, prints the log
path and exit status, and exits with the validator's exact status. It owns the
check's cwd, environment, cancellation forwarding, and bounded log retention;
do not compose shell setup around it. When the check cwd is inside a repository
with `.nvmrc`, it also runs the validator through NVM with that selector and
fails before the validator starts if the pinned runtime cannot be resolved.
Use `--env PATH="...:$PATH"` for additional tool directories or repositories
without `.nvmrc`; an `.nvmrc` remains the canonical Node selector when present.

1. Never use `fireAndForget`, shell `&`, or a detached task for checks -- an
   unattended process can fail while the model sleeps or polls stale output.
2. Never use `cd`, leading shell assignments, redirects, or pipes around a
   check, including through `tee`, `tail`, `head`, or `rg` -- `run-check`
   already owns live display and persistence.
3. Never append `sleep`, `tail`, `rg`, `echo $?`, or any other shell action
   after a check -- the attached tool result is the complete evidence.
4. Never cancel a quiet check to inspect its log. Wait for the foreground
   call. If the user cancels it, record the run as interrupted, not failed.
5. Never re-run a check to change the visible slice; there is no slice.

The `check_guard` hook denies recognized validators that bypass this shape,
including in `droid exec` (where a violation intentionally ends the run). It
is a cooperation guard, not a Bash sandbox.

## Pre-check: worktree environment

```bash
MAIN_REPO=$(git worktree list | head -1 | awk '{print $1}')
[ "$(git rev-parse --show-toplevel)" != "$MAIN_REPO" ] && echo "WORKTREE"
```

If in a worktree, follow the **worktree-setup** skill before any checks.
Never `npm install` or `pip install` in a worktree.

## Run all detected checks

Detect tooling from root and affected-workspace configs and package scripts,
then run each applicable check. Every "Typical command" below is validator
argv placed after `run-check ... --`:

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

`evidence` = command run (+ `run-check` log path), workflow/config path
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
`knip --workspace <pkg>`, `tsc -p <pkg>`, `vulture <paths>`) with `--cwd`
when package-local config requires it. Skipping it or running it unscoped both
ship as `no signal` lies.

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
