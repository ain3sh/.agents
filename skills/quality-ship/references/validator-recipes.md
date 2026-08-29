# Validator Recipes

Exact invocations and known dead ends for the heavier validators. Policy
(when each runs, what blocks) lives in `SKILL.md`; this file is the how.

## Output capture: file-first, never inline-filter

Anti-pattern: `<check> 2>&1 | rg "FAIL|Tests " | head -6`. It guesses in
advance -- and irrevocably -- which slice of output matters. A wrong guess
(JSON log lines matching `Tests `, expected error-path logs matching
`error `) destroys the evidence, and the only recovery is re-running the
whole suite with a new guess. Two bonus lies: `$?` after a pipeline is the
last filter's exit code (rg/head), not the runner's, and `head` closing the
pipe early can SIGPIPE-kill the runner mid-suite while the pipeline still
exits 0.

Canonical shape -- capture first, then a small visible slice:

```bash
npx vitest run <paths> 2>&1 | tee /tmp/qs-test.log | tail -n 30
<scoped-lint-command> 2>&1 | tee /tmp/qs-lint.log | tail -n 30
```

- `tail` as the visible slice: Vitest/Jest/ESLint/Oxlint/Oxfmt summaries print
  at the end.
- For anything else, query the log (`rg -n -C3 FAIL /tmp/qs-test.log`, Read).
  Re-querying a file is free; re-running a suite is not.
- Need the runner's real exit code: `set -o pipefail` first (bash/zsh), or
  read the summary lines from the log.

The `capture` hook enforces the shape: recognized validators piped through
filters without capture get **denied** (interactively), with the exact tee'd
re-run command in the deny reason; in `droid exec`, where a deny would kill
the run, the command runs and a corrective PostToolUse note carries the same
re-run command. After a captured run, the PostToolUse pass points you at the
log. It only fires on validator-led pipeline segments with no existing
capture -- `curl ... | bash`, `git log | rg`, already-tee'd or
file-redirected commands pass through untouched. The validator vocabulary is
the `tools` list under `[hooks.pre_tool_use.capture]` in `configs/droid.toml`
(includes oxlint/oxfmt) plus structural runner patterns (npm/pnpm/yarn/bun
`run <test|lint|typecheck|check|build>`, turbo, go/cargo/make checks); for a
validator it doesn't recognize, add it to that list -- and tee manually in
the moment. Toggle/log dir live in the same section.

## Oxfmt and Oxlint

Detect both config files and package scripts. A repository may deliberately
run multiple configs or both Oxlint and ESLint; do not replace the canonical
sequence with one direct command.

Scoped direct shapes:

```bash
oxfmt --write --threads=1 <paths>
oxfmt --check --threads=1 <paths>
oxlint --fix --threads=1 <paths>
oxlint --threads=1 <paths>
```

- Resolve the repository-installed binary through its package manager when it
  is not already on `PATH`; never let an executor install a missing validator
  inside a shared worktree.
- Oxfmt writes by default; use `--check` for verification-only runs.
- Do not use Oxlint's `--fix-dangerously` unless the repository explicitly
  approves behavior-changing fixes.
- Do not invent `-c <config>` when the package script omits it. Explicit config
  selection can bypass a separate root or auto-discovered config pass.
- Keep resource limits from repository instructions. `--threads=1` is the
  safe default for shared machines and narrow checks.

## Documentation validation

Formatting, Markdown linting, and link checking are independent checks. Run
every configured owner; a formatter does not enforce Markdown structure, and
a Markdown linter does not verify link targets.

| Check | Common signals | Scoped shape |
|---|---|---|
| Format | formatter config/script that includes Markdown | use the configured formatter on changed docs |
| Markdown lint | `.markdownlint*`, `markdownlint-cli2` config/script/workflow, `remark` config/script | configured script / `markdownlint-cli2 <paths>` / `remark <paths>` |
| Links | `lychee.toml`, `.lycheeignore`, Lychee script/workflow/action | configured script / `lychee <configured-args> <paths>` |

- Prefer the configured script. Markdown globs, ignores, custom rules, and
  plugin loading are part of the gate.
- Preserve Lychee's configured mode and arguments. Offline mode, fragment
  checks, root directory, accepted status codes, and exclusions materially
  change what it validates.
- A link checker may intentionally scan all docs because fragments and
  relative links cross file boundaries. Do not narrow a repo-wide configured
  gate unless its command supports equivalent changed-file scoping.
- If the check exists only in CI and no local runner is available without an
  install or CI emulation, record `ci-only` with the workflow/config path.
  Never report `no signal`.
- Treat workflow-specific documentation checks (generated indexes, line
  ceilings, schema checks) as additional signals; do not assume
  Markdownlint/Lychee subsume them.

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

## Monorepo scoping: identify the flag owner

`--` separates package-manager arguments from arguments passed to the script.
The correct side depends on which process owns the scope flag:

| Scope owner | Shape |
|---|---|
| npm workspace selection | `npm run <task> --workspace=<pkg>` (`-w <pkg>`) |
| pnpm workspace selection | `pnpm --filter <pkg> <task>` |
| yarn workspace selection | `yarn workspace <pkg> <task>` |
| direct Turbo | `turbo run <task> --filter=<pkg>` |
| Turbo behind an npm script | `npm run <task> -- --filter=<pkg>` |
| test/lint tool behind a package script | `npm run <task> -- <tool-flags> <paths>` |

Inspect the script before choosing:

```bash
# Root script delegates to Turbo: Turbo owns --filter, so pass it through.
npm run test -- --filter=@scope/pkg

# Run the package's own script: npm owns --workspace.
npm run test --workspace=@scope/pkg -- src/foo.test.ts

# Direct Turbo invocation.
turbo run test --filter=@scope/pkg -- src/foo.test.ts
```

Wrong:

```bash
# npm consumes/ignores the unknown placement; Turbo never receives the filter.
npm run test --filter=@scope/pkg
```

Do not bypass a canonical root or package script merely because `turbo.json`
exists. Scripts may supply env, heap limits, cwd-sensitive config, or multiple
validators. If a scoped run takes unexpectedly long, inspect the script and
process owning each flag before blaming the repo.

Derive affected packages from `git diff --name-only` vs the base.

**Cwd-sensitive configs:** some tools resolve config from their working
directory, making `cd` into the package required rather than a last resort.
For example, package-local path aliases may resolve only when ESLint runs from
that package; invoking it from the root can produce false
`import/no-unresolved` errors.

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
