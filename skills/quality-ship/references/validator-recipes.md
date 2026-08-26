# Validator Recipes

Exact invocations and known dead ends for the heavier validators. Policy
(when each runs, what blocks) lives in `SKILL.md`; this file is the how.

## slop-scan delta (AI-slop, JS/TS)

Run on **temp dirs containing only the changed files**, then delete them:

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
- **Never point `--base`/`--head` at full checkouts** (main repo, a worktree). It walks the entire tree -- `node_modules`, build output, everything -- and times out (240s+) even with a pile of `--ignore` globs. The changed-files temp dirs above finish in seconds.

Triage findings alongside lint/typecheck output: slop-scan catches the 15
deterministic slop patterns (swallowed errors, placeholder comments, generic
`Record<string, unknown>` casts, pass-through wrappers, duplicate signatures,
etc.) that lint and typecheck miss.

## react-doctor (React correctness/perf)

```bash
react-doctor . --scope changed --base <base-ref> --verbose
```

Different axis from slop-scan: slop-scan flags structural noise, react-doctor
flags concrete React correctness/perf bugs (effect chains, derived state,
fetch-in-effect, missing Suspense around `useSearchParams`, server-fn input
validation, etc.). See the **react-doctor** skill for category-gated triage
policy, false-positive handling, and config.

## Monorepo scoping: the right flag, in the right position

Scope flags belong to the **runner**, so they go **before** `--`. Put one
after and it gets silently handed to the underlying tool (which ignores it),
and the validator runs against the whole repo. Each runner uses a different
flag:

| Runner | Scope flag |
|--------|-----------|
| npm    | `--workspace=<pkg>` (`-w <pkg>`) |
| pnpm   | `--filter <pkg>` |
| yarn   | positional: `yarn workspace <pkg> <task>` |
| turbo  | `--filter=<pkg>` |

**The trap that keeps biting**: droids borrow turbo's `--filter` for npm and
stick it after `--`:

```bash
# WRONG: `--filter` isn't an npm flag; after `--` it's passed to tsc,
# which ignores it and typechecks the WHOLE repo (looks scoped, isn't).
npm run typecheck -- --filter=@factory/cli

# RIGHT
npm run typecheck --workspace=@factory/cli   # or: -w @factory/cli
turbo run typecheck --filter=@factory/cli    # prefer when turbo.json exists
```

The failure is silent (exit 0 or timeout). If a "scoped" check runs
unexpectedly long, suspect the flag is in the wrong place or wrong dialect
before blaming the repo.

Prefer turbo when `turbo.json` is present (it picks up workspace-level config
that direct invocation misses); otherwise use the table. Last resort: `cd`
into the package and run there. Derive affected packages from
`git diff --name-only` vs the base.

**Cwd-sensitive configs:** some tools resolve config from their working
directory, making `cd` into the package required rather than a last resort.
Known case: factory-mono `apps/cli`'s `@/` aliases only resolve when ESLint
runs from `apps/cli`; from the root you get false `import/no-unresolved`
errors.

## Test runners: serial flags and concurrency mitigations

| Runner | Serial flag |
|--------|-------------|
| Jest | `--runInBand` (`-i`) |
| Vitest | `--no-file-parallelism` |
| Playwright | `--workers=1` |
| pytest + xdist | `-p no:xdist` |

Serial workers are the default on subset runs: no pool startup cost, no OOM
when droids share a host. Forward flags + paths past the script/task boundary
with `--`:

```bash
npm test -- --runInBand --findRelatedTests src/foo.ts
pnpm vitest run --no-file-parallelism src/foo.test.ts
turbo run test --filter=@app/web -- --runInBand src/foo.test.ts
```

Additional mitigations when concurrent droid activity is likely:

- **Mutex**: `flock -w 600 /tmp/droid-tests.lock <cmd>` -- one test run at a time across droid instances.
- **Heap cap**: `NODE_OPTIONS=--max-old-space-size=2048` -- fail fast instead of swap-thrashing.
- **Deprioritize**: prefix with `nice -n 10 ionice -c3` when another runner is already active.
