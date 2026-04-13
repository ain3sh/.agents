---
name: worktree-setup
description: "Git worktree environment setup. ALWAYS check for worktree context before running any tooling (lint, test, build, dev server). Triggers on: working directory contains 'worktree', node_modules or .venv is missing, 'Cannot find module' errors, npm install fails with lockfile conflicts, pytest/jest can't find dependencies."
---

# Worktree Setup

## First Step: Always Check

**Before running any tooling** (lint, test, build, typecheck, dev server), check if you're in a worktree:

```bash
MAIN_REPO=$(git worktree list | head -1 | awk '{print $1}')
if [ "$(git rev-parse --show-toplevel)" != "$MAIN_REPO" ]; then
  echo "WORKTREE DETECTED -- symlink deps before proceeding"
fi
```

Path heuristic: if the working directory contains `worktree` (e.g., `factory-mono-worktrees/fac-17658`), assume worktree and symlink immediately.

## Rule: Never Install Dependencies in a Worktree

Worktrees share `.git` with the main repo but have their own working tree. Running `npm install` or `pip install` in a worktree is **always wrong** -- it's slow, creates lockfile/env conflicts, and duplicates large dependency trees.

**Reuse the main repo's dependencies, but make workspace package resolution point at the worktree.**

## JS/TS Monorepo Setup: Prefer a Symlink-Tree Mirror, Not a Root Symlink

In JS/TS monorepos, a plain root symlink like this:

```bash
ln -sf "$MAIN_REPO/node_modules" node_modules
```

can still cause TypeScript/Jest/Bundlers to resolve workspace packages back to the **main repo source tree** instead of the worktree. That mixes main-repo and worktree sources and can surface stale exports or inconsistent types.

Prefer a **local symlink-tree mirror** at the worktree root:

```bash
MAIN_REPO=$(git worktree list | head -1 | awk '{print $1}')
WORKTREE=$(git rev-parse --show-toplevel)

rm -f "$WORKTREE/node_modules"
mkdir -p "$WORKTREE/node_modules"
cp -as "$MAIN_REPO/node_modules/." "$WORKTREE/node_modules/"
```

This preserves the main repo's installed dependency tree, but gives you a local `node_modules` directory whose workspace links you can safely rewrite.

## Repoint Workspace Packages to the Worktree

After creating the root symlink-tree mirror, repoint local workspace packages so imports resolve to the **current worktree**:

```bash
MAIN_REPO=$(git worktree list | head -1 | awk '{print $1}')
WORKTREE=$(git rev-parse --show-toplevel)

mkdir -p "$WORKTREE/node_modules/@factory"

# Example manual rewires
ln -sfn "$WORKTREE/packages/common" "$WORKTREE/node_modules/@factory/common"
ln -sfn "$WORKTREE/packages/logging" "$WORKTREE/node_modules/@factory/logging"
ln -sfn "$WORKTREE/packages/frontend" "$WORKTREE/node_modules/@factory/frontend"
```

If the repo has many local workspace packages, generate these links automatically from `apps/*` and `packages/*` package.json files rather than patching them one-by-one.

## Symlink Granularity

Monorepos often also have **nested** `node_modules` per package. A worktree-root mirror is necessary, but it may still not be sufficient if validators run from a subpackage. Rewire at the level where the tooling expects to find dependencies:

```bash
MAIN_REPO=$(git worktree list | head -1 | awk '{print $1}')
WORKTREE=$(git rev-parse --show-toplevel)

# Per-package: mirror or symlink the specific subpackage you're working in
# e.g., if running tests in apps/my-package:
rm -rf "$WORKTREE/apps/my-package/node_modules"
mkdir -p "$WORKTREE/apps/my-package/node_modules"
cp -as "$MAIN_REPO/apps/my-package/node_modules/." \
  "$WORKTREE/apps/my-package/node_modules/"
```

**If subpackage tests fail with "Cannot find module" but root commands work, the subpackage needs its own local mirror or targeted links.** Start with the specific package you're working in; only broaden if needed.

### Hoisted vs package-local dependencies

In npm workspaces, a missing module in a worktree does **not** always mean the dependency is absent from the main repo. Some validator-only dependencies may exist only in the package-local tree (for example `apps/my-package/node_modules`) and not at the root.

**Troubleshooting order:**

1. Mirror root `node_modules`
2. Run the validator
3. If a module is missing, check whether it exists under the main repo's package-local `node_modules`
4. Mirror or selectively link that package-level `node_modules`
5. Re-run the validator

Example:

```bash
MAIN_REPO=$(git worktree list | head -1 | awk '{print $1}')
WORKTREE=$(git rev-parse --show-toplevel)
test -d "$MAIN_REPO/apps/my-package/node_modules/some-validator-dependency" && \
  mkdir -p "$WORKTREE/apps/my-package/node_modules" && \
  cp -as "$MAIN_REPO/apps/my-package/node_modules/." \
    "$WORKTREE/apps/my-package/node_modules/"
```

### E2E caveat: full package symlinks can break some harnesses

Some end-to-end tooling traverses or copies `node_modules` and can fail when the entire package-level tree is a symlink. If a full package symlink causes E2E failures, fall back to **targeted module symlinks** instead of linking the whole directory.

Example:

```bash
MAIN_REPO=$(git worktree list | head -1 | awk '{print $1}')
mkdir -p apps/my-package/node_modules/@vendor
ln -sf "$MAIN_REPO/apps/my-package/node_modules/@vendor/test-helper" \
  apps/my-package/node_modules/@vendor/test-helper
```

## Transitive Workspace Dependency Caveat

Even if you changed only one package, its **transitive workspace dependencies** may still resolve to the main repo unless their workspace links are also repointed. If type errors look impossible or exports appear stale, suspect mixed source resolution before changing code.

Common example: `apps/cli` resolves `@factory/logging`, which then resolves `@factory/common`. If `@factory/logging` points at the main repo, `@factory/common` may also resolve there.

## Verification

Before trusting validator output, verify that resolution points at the worktree:

```bash
tsc --noEmit --traceResolution -p apps/my-package/tsconfig.json | \
  rg "@factory/common|@your-scope/"
```

You want resolved paths under the **worktree** root, not the main repo root.

## Python / venv

Same principle. Never `pip install` or `python -m venv` in a worktree.

```bash
MAIN_REPO=$(git worktree list | head -1 | awk '{print $1}')

# Symlink .venv
[ -d "$MAIN_REPO/.venv" ] && [ ! -e ".venv" ] && ln -sf "$MAIN_REPO/.venv" .venv

# Or if using a named venv directory
[ -d "$MAIN_REPO/venv" ] && [ ! -e "venv" ] && ln -sf "$MAIN_REPO/venv" venv
```

Activate via the symlink as normal: `source .venv/bin/activate`.

## Failure Modes and Fixes

| Symptom | Cause | Fix |
|---------|-------|-----|
| "Cannot find module X" | Missing root mirror, package-local mirror, or targeted link | Mirror or link the relevant `node_modules` location |
| Validator sees stale exports or impossible type errors | Some workspace packages resolve to the main repo while others resolve to the worktree | Repoint workspace package links in `node_modules/@scope/*` to the worktree |
| Validator can't find a package that exists in the main repo | Dependency is package-local, not hoisted to the root | Check `apps/<pkg>/node_modules` in the main repo and mirror or link that package tree |
| `npm install` runs for minutes, lockfile conflicts | Ran install in worktree | Delete local `node_modules` + `package-lock.json`, symlink instead |
| Tests pass at root but fail in subpackage | Root mirror exists but subpackage-local deps are missing | Add a package-local mirror or targeted links |
| E2E tooling fails while traversing or copying `node_modules` | Full package-level symlink is incompatible with the harness | Replace the full package symlink with targeted module symlinks |
| `ModuleNotFoundError` in Python | Missing `.venv` symlink | Symlink `.venv` from main repo |
| Turbo cache misses every run | Turbo hashes `node_modules` path | Local mirrors/symlinks stabilize paths inside the worktree |
