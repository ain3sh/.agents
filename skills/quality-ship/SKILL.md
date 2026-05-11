---
name: quality-ship
description: Shared atom for running quality checks, committing, and pushing. Background knowledge for workflow commands -- not invoked directly.
user-invocable: false
---

# Quality Checks + Ship

## Quality Checks

### Pre-check: worktree environment

Before running any checks, determine if you're in a git worktree:

```bash
MAIN_REPO=$(git worktree list | head -1 | awk '{print $1}')
[ "$(git rev-parse --show-toplevel)" != "$MAIN_REPO" ] && echo "WORKTREE"
```

If in a worktree, follow the **worktree-setup** skill to symlink dependencies before proceeding. Never `npm install` or `pip install` in a worktree.

### Run all detected checks

Detect the project's tooling from config files at the repo root, then run each applicable check:

| Check | Detection signals | Typical command |
|-------|-------------------|-----------------|
| Format | `.prettierrc*`, `biome.json`, `dprint.json` | `npm run format --write` or `npx prettier --write` or equivalent |
| Lint fix | `eslint.config*`, `.eslintrc*`, `biome.json` | `npm run fix` or `npx eslint --fix` |
| Dead code (JS/TS) | `knip.*`, `knip` in package.json scripts | `npm run knip` or `npx knip` |
| Dead code (Python) | `*.py` in diff + `pyproject.toml` / `setup.py` | `vulture <changed-paths>` (or `uvx vulture`) |
| AI-slop (JS/TS) | any `*.{js,jsx,ts,tsx}` in diff | `slop-scan delta <base> <head> --format json` |
| React diagnostics (JS/TS) | `react`/`react-dom`/`next`/`@remix-run/*` in `package.json` | `npx -y react-doctor@latest . --diff <base> --verbose` |
| Type check | `tsconfig.json` | `npm run typecheck` or `npx tsc --noEmit` |
| Tests | `jest.config*`, `vitest.config*`, `pytest.ini` | Changed-file subset, serial workers (see below) |

- Inspect `package.json` scripts (or `pyproject.toml` / `Makefile` for Python) for canonical commands (`format`, `fix`, `lint`, `knip`, `test`, `typecheck`).
- Fix any issues found. Re-run until clean.

**Mandatory gate -- before committing, emit a checklist covering the worktree pre-check and every row in the table above:**

```
quality-ship checklist:
- worktree:  <main | repaired> (evidence)
- format:    <ran | no signal> (evidence)
- lint:      <ran | no signal> (evidence)
- dead-code: <ran | no signal> (evidence)
- ai-slop:   <ran | no signal> (evidence)
- react:     <ran | no signal> (evidence)
- typecheck: <ran | no signal> (evidence)
- tests:     <ran | no signal> (evidence)
```

`evidence` = command run or missing config (validators); detection output + `repair.py` invocation (worktree). Don't commit until every line is filled. CI gates each validator; the worktree row catches repair gaps that surface as `Cannot find module` mid-validator. When detection emits `WORKTREE`, `worktree: repaired` is the only valid tag -- not "looks fine, skipped".

### AI-slop detector (deterministic)

For any PR touching JS/TS files, run `slop-scan delta <base-ref> <head-ref> --format json` and triage the findings alongside lint/typecheck output. It catches the 15 deterministic slop patterns (swallowed errors, placeholder comments, generic `Record<string, unknown>` casts, pass-through wrappers, duplicate signatures, etc.) that lint and typecheck miss. Treat any new violations as blocking — do not commit slop.

### React diagnostics (rules-based)

For any PR touching a React codebase (signal: `react`/`react-dom`/`next`/`@remix-run/*` in `package.json`), run `npx -y react-doctor@latest . --diff <base-ref> --verbose` and triage alongside the AI-slop output. Different axes: slop-scan flags structural noise, react-doctor flags concrete React correctness/perf bugs (effect chains, derived state, fetch-in-effect, missing Suspense around `useSearchParams`, server-fn input validation, etc.). See the **react-doctor** skill for category-gated triage policy, false-positive handling, and config. New errors are blocking; warnings are blocking when the category is `security`, `correctness`, `state-and-effects`, or `server` -- advisory for `design`.

### Serial test execution

Default to serial workers — no pool startup cost on subset runs, no OOM when droids share a host. Select the subset with positional paths (all runners); Jest also has `--findRelatedTests` for import-graph-aware selection.

| Runner | Serial flag |
|--------|-------------|
| Jest | `--runInBand` (`-i`) |
| Vitest | `--no-file-parallelism` |
| Playwright | `--workers=1` |
| pytest + xdist | `-p no:xdist` |

Forward flags past the script/task boundary with `--`:

```bash
npm test -- --runInBand --findRelatedTests src/foo.ts
pnpm vitest run --no-file-parallelism src/foo.test.ts
turbo run test --filter=@app/web -- --runInBand
```

Additional mitigations when concurrent droid activity is likely:

- **Mutex**: `flock -w 600 /tmp/droid-tests.lock <cmd>` — one test run at a time across droid instances.
- **Heap cap**: `NODE_OPTIONS=--max-old-space-size=2048` — fail fast instead of swap-thrashing.
- **Deprioritize**: prefix with `nice -n 10 ionice -c3` when another runner is already active.

### Monorepo scoping: use turbo, not direct invocation

In monorepos with `turbo.json`, **always** use `turbo run <task> --filter=<package>` instead of direct tool invocation for **all** checks: `format`, `lint`, `knip`, `typecheck`, and `test`. Direct invocation misses workspace-level configuration (path aliases, package-scoped configs) and runs against the entire repo unnecessarily.

In monorepos without turbo, scope validators to the changed packages. Use `git diff --name-only` against the base branch to identify affected packages, then run checks from within those package directories.

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
