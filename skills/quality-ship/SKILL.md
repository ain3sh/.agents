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
| Format | `.prettierrc*`, `biome.json`, `dprint.json` | `npx prettier --write <paths>` / `biome format --write <paths>` (prefer over a bundled `npm run format`) |
| Lint fix | `eslint.config*`, `.eslintrc*`, `biome.json` | `npx eslint --fix <paths>` / `biome lint --apply <paths>` (prefer over a bundled `npm run fix`) |
| Dead code (JS/TS) | `knip.*`, `knip` in package.json scripts | `npx knip --workspace <pkg>` (monorepo) / `npx knip` (single pkg) |
| Dead code (Python) | `*.py` in diff + `pyproject.toml` / `setup.py` | `vulture <changed-paths>` (or `uvx vulture`) |
| AI-slop (JS/TS) | any `*.{js,jsx,ts,tsx}` in diff | `slop-scan delta <base-dir> <head-dir> --json` on changed-files temp dirs (see below) |
| React diagnostics (JS/TS) | `react`/`react-dom`/`next`/`@remix-run/*` in `package.json` | `npx -y react-doctor@latest . --diff <base> --verbose` |
| Type check | `tsconfig.json` | `npx tsc --noEmit -p <pkg>` (or runner-scoped per Monorepo scoping) |
| Tests | `jest.config*`, `vitest.config*`, `pytest.ini` | Changed-file subset, serial workers (see below) |

- Inspect `package.json` scripts (or `pyproject.toml` / `Makefile` for Python) to learn *which* tools the repo uses, but **prefer invoking each tool directly** (`npx prettier`, `npx eslint`, `npx tsc`, `npx knip`) scoped to changed paths.
- **Avoid aggregate "fix everything" scripts.** A bundled task like `npm run fix` / `npm run check` (e.g. factory-mono's) chains formatter + linter + typecheck + more across the whole repo and can take many minutes. Run the individual tools you actually need, scoped to the diff, instead. Only fall back to the aggregate script if a tool genuinely can't be invoked directly (missing binary, wrapper-only config) — and note that reason in the checklist evidence.
- Fix any issues found. Re-run until clean.

### Fix the cause, don't suppress the validator

A failing validator is signal: assume it's right and fix the underlying code — remove the dead export knip found, narrow the type instead of casting, handle the swallowed error. Silencing it just ships the problem.

These escape hatches are last resorts, not default moves — reach for one only when the rule is a genuine false positive on that specific line, then scope it as narrowly as possible with a comment justifying *why* it's safe:

- `eslint-disable[-next-line]` or per-rule config overrides
- knip `ignore` / `ignoreDependencies` entries
- `// @ts-ignore`, `// @ts-expect-error`, looser `tsconfig` strictness
- `# noqa`, `# type: ignore`, vulture whitelists, `# pragma: no cover`
- skipping / `.only` / `xfail` on tests to force green

**Mandatory gate -- before committing, emit a checklist covering the worktree pre-check and every row in the table above:**

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

`evidence` = command run or missing config (validators); detection output + `repair.py` invocation (worktree). Don't commit until every line is filled. CI gates each validator; the worktree row catches repair gaps that surface as `Cannot find module` mid-validator. When detection emits `WORKTREE`, `worktree: repaired` is the only valid tag -- not "looks fine, skipped".

`no signal` means the tool is **genuinely not configured** in the repo, not that a convenient scoped script is missing. When the tool exists but the package.json has no pre-wired scoped task (`knip:cli`, `typecheck:web`), you have two equally wrong escape hatches: skipping it, or running it unscoped against the whole repo. Both ship as `no signal` lies. Scope it yourself with the tool's own flags (`knip --workspace <pkg>`, `eslint <paths>`, `tsc -p <pkg>`, `vulture <paths>`) or by `cd`ing into the package directory. A "scoped" validator that took minutes is the giveaway that you actually ran the full repo, see Monorepo scoping for why.

### AI-slop detector (deterministic)

For any diff touching JS/TS files, run `slop-scan delta` on **temp dirs containing only the changed files**, then delete them:

```bash
BASE=$(git merge-base origin/<target> HEAD)
TMP=$(mktemp -d)
git diff --name-only --diff-filter=d "$BASE" -- '*.js' '*.jsx' '*.ts' '*.tsx' | while read -r f; do
  mkdir -p "$TMP/base/$(dirname "$f")" "$TMP/head/$(dirname "$f")"
  git show "$BASE:$f" > "$TMP/base/$f" 2>/dev/null || rm -f "$TMP/base/$f"  # new file: no base version
  cp "$f" "$TMP/head/$f"                                                    # working tree = what you're about to commit
done
slop-scan delta "$TMP/base" "$TMP/head" --json --fail-on added,worsened
rm -rf "$TMP"
```

Known dead ends (both burned real sessions):

- `delta` takes **directory paths as positionals**, not git refs, and JSON output is `--json`. `slop-scan delta origin/dev HEAD --format json` fails with `Unexpected extra positional arguments: json` (and would have scanned nothing useful anyway).
- **Never point `--base`/`--head` at full checkouts** (main repo, a worktree). It walks the entire tree — `node_modules`, build output, everything — and times out (240s+) even with a pile of `--ignore` globs. The changed-files temp dirs above finish in seconds.

If the file list is empty, skip the check (`no signal`). Triage findings alongside lint/typecheck output: slop-scan catches the 15 deterministic slop patterns (swallowed errors, placeholder comments, generic `Record<string, unknown>` casts, pass-through wrappers, duplicate signatures, etc.) that lint and typecheck miss. Treat any new violations as blocking — do not commit slop.

### React diagnostics (rules-based)

For any PR touching a React codebase (signal: `react`/`react-dom`/`next`/`@remix-run/*` in `package.json`), run `npx -y react-doctor@latest . --diff <base-ref> --verbose` and triage alongside the AI-slop output. Different axes: slop-scan flags structural noise, react-doctor flags concrete React correctness/perf bugs (effect chains, derived state, fetch-in-effect, missing Suspense around `useSearchParams`, server-fn input validation, etc.). See the **react-doctor** skill for category-gated triage policy, false-positive handling, and config. New errors are blocking; warnings are blocking when the category is `security`, `correctness`, `state-and-effects`, or `server` -- advisory for `design`.

### Repo conventions (documented)

Validators cover mechanics; they're blind to the idioms a repo documents in prose (error handling, file organization, test placement, flags) -- the rules reviewers flag once the gate is green. Follow the **repo-conventions** skill: discover, diff-scope, apply, emit the `conventions:` row. `no signal` only when the repo documents none -- not when reading was inconvenient.

### Monorepo scoping: the right flag, in the right position

Scope flags belong to the **runner**, so they go **before** `--`. Put one after and it gets silently handed to the underlying tool (which ignores it), and the validator runs against the whole repo. Each runner uses a different flag:

| Runner | Scope flag |
|--------|-----------|
| npm    | `--workspace=<pkg>` (`-w <pkg>`) |
| pnpm   | `--filter <pkg>` |
| yarn   | positional: `yarn workspace <pkg> <task>` |
| turbo  | `--filter=<pkg>` |

**The trap that keeps biting**: droids borrow turbo's `--filter` for npm and stick it after `--`:

```bash
# WRONG: `--filter` isn't an npm flag; after `--` it's passed to tsc,
# which ignores it and typechecks the WHOLE repo (looks scoped, isn't).
npm run typecheck -- --filter=@factory/cli

# RIGHT
npm run typecheck --workspace=@factory/cli   # or: -w @factory/cli
turbo run typecheck --filter=@factory/cli    # prefer when turbo.json exists
```

The failure is silent (exit 0 or timeout). If a "scoped" check runs unexpectedly long, suspect the flag is in the wrong place or wrong dialect before blaming the repo.

Prefer turbo when `turbo.json` is present (it picks up workspace-level config that direct invocation misses); otherwise use the table. Last resort: `cd` into the package and run there. Derive affected packages from `git diff --name-only` vs the base.

### Test scoping: package scope is NOT enough

**This is about how you *run* tests to validate a diff (execution scope), not how broad the tests you *author* should be (coverage).** A feature's acceptance test or a bug's contract-level regression can legitimately span components or run under stress (see **consolidate-test-suites**); never let "run narrow" leak into "write narrow."

**HARD RULE: never run a full test suite to validate a diff. No exceptions without an explicit reason logged in the checklist.** A bare `npm test` / `run test` / `turbo run test` with no path argument is a defect — stop and re-scope before it runs. If you catch yourself about to execute an unscoped suite, that is the bug the user keeps yelling about.

Tests have **two** scope axes and you need both. The package filter (`--workspace` / turbo `--filter`) picks *which suite*; it does **not** narrow *which tests* — `run test` on a package still executes that package's entire suite (wiki, unrelated parsers, everything). Running the whole suite to validate a small diff is the mistake: slow, noisy, irrelevant. **Every test invocation MUST carry a changed-file subset.** No path argument = wrong command.

- **Subset (mandatory)**: positional test paths (all runners), or Jest `--findRelatedTests <changed src files>` for import-graph-aware selection. Derive paths from `git diff --name-only` vs the base.
- **Serial workers (default)**: no pool startup cost on subset runs, no OOM when droids share a host.

| Runner | Serial flag |
|--------|-------------|
| Jest | `--runInBand` (`-i`) |
| Vitest | `--no-file-parallelism` |
| Playwright | `--workers=1` |
| pytest + xdist | `-p no:xdist` |

Forward flags + paths past the script/task boundary with `--`:

```bash
npm test -- --runInBand --findRelatedTests src/foo.ts
pnpm vitest run --no-file-parallelism src/foo.test.ts
turbo run test --filter=@app/web -- --runInBand src/foo.test.ts
```

Full-suite runs are **CI's job, never yours**. The only time you run a whole package suite locally is a genuinely cross-cutting change (shared util, config, or types imported by most of the package) — and when you do, you must say so explicitly in the checklist evidence (`tests: full-suite (reason: <why>)`). Absent that logged justification, a full-suite run is wrong.

Additional mitigations when concurrent droid activity is likely:

- **Mutex**: `flock -w 600 /tmp/droid-tests.lock <cmd>` — one test run at a time across droid instances.
- **Heap cap**: `NODE_OPTIONS=--max-old-space-size=2048` — fail fast instead of swap-thrashing.
- **Deprioritize**: prefix with `nice -n 10 ionice -c3` when another runner is already active.

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
