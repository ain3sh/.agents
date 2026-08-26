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

## Run all detected checks

Detect the project's tooling from config files at the repo root, then run each applicable check:

| Check | Detection signals | Typical command |
|-------|-------------------|-----------------|
| Format | `.prettierrc*`, `biome.json`, `dprint.json` | `npx prettier --write <paths>` / `biome format --write <paths>` |
| Lint fix | `eslint.config*`, `.eslintrc*`, `biome.json` | `npx eslint --fix <paths>` / `biome lint --apply <paths>` |
| Dead code (JS/TS) | `knip.*`, `knip` in package.json scripts | `npx knip --workspace <pkg>` (monorepo) / `npx knip` |
| Dead code (Python) | `*.py` in diff + `pyproject.toml` / `setup.py` | `vulture <changed-paths>` (or `uvx vulture`) |
| AI-slop (JS/TS) | any `*.{js,jsx,ts,tsx}` in diff | `slop-scan delta` on changed-files temp dirs (recipe in references) |
| React diagnostics | `react`/`react-dom`/`next`/`@remix-run/*` in `package.json` | `react-doctor . --scope changed --base <base> --verbose` |
| Type check | `tsconfig.json` | `npx tsc --noEmit -p <pkg>` |
| Tests | `jest.config*`, `vitest.config*`, `pytest.ini` | Changed-file subset, serial workers (rules below) |

- Inspect `package.json` scripts (or `pyproject.toml` / `Makefile`) to learn *which* tools the repo uses, but **invoke each tool directly**, scoped to changed paths.
- **Avoid aggregate "fix everything" scripts** (`npm run fix` / `npm run check`): they chain every tool across the whole repo and can take minutes. Fall back to one only when a tool genuinely can't be invoked directly -- and note that reason in the checklist evidence.
- Fix any issues found. Re-run until clean.

## Fix the cause, don't suppress the validator

A failing validator is signal: assume it's right and fix the underlying code -- remove the dead export knip found, narrow the type instead of casting, handle the swallowed error. Silencing it just ships the problem.

Escape hatches (`eslint-disable`, knip `ignore*`, `@ts-ignore`/`@ts-expect-error`, looser `tsconfig`, `# noqa`/`# type: ignore`/vulture whitelists/`# pragma: no cover`, test skips/`.only`/`xfail`) are last resorts for genuine false positives on a specific line -- scoped as narrowly as possible, with a comment justifying *why* it's safe.

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
- dead-code: <ran | no signal> (evidence)
- ai-slop:   <ran | no signal> (evidence)
- react:     <ran | no signal> (evidence)
- conventions: <applied | no signal> (evidence)
- typecheck: <ran | no signal> (evidence)
- tests:     <ran | no signal> (evidence)
```

`evidence` = command run or missing config (validators); detection output + `repair.py` invocation (worktree). Don't commit until every line is filled. When detection emits `WORKTREE`, `worktree: repaired` is the only valid tag -- not "looks fine, skipped".

`no signal` means the tool is **genuinely not configured** in the repo, not that a convenient scoped script is missing. When the tool exists but no pre-wired scoped task does, scope it yourself with the tool's own flags (`knip --workspace <pkg>`, `eslint <paths>`, `tsc -p <pkg>`, `vulture <paths>`) or by `cd`ing into the package. Skipping it or running it unscoped both ship as `no signal` lies.

## Scoping rules

1. **Scope flags belong to the runner, before `--`.** After `--` they're silently ignored and the validator runs against the whole repo (exit 0, looks scoped, isn't). Per-runner dialects and the npm/turbo trap: references.
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
