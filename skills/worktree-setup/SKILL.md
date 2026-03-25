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

**Symlink from the main repo instead.**

## Symlink Granularity

Monorepos often have **nested** `node_modules` per package. A root-only symlink is not enough if tests run from a subpackage. Symlink at the level where the tooling expects to find dependencies:

```bash
MAIN_REPO=$(git worktree list | head -1 | awk '{print $1}')

# 1. Always: root node_modules
ln -sf "$MAIN_REPO/node_modules" node_modules

# 2. Per-package: symlink the specific subpackage you're working in
# e.g., if running tests in apps/cli:
ln -sf "$MAIN_REPO/apps/cli/node_modules" apps/cli/node_modules
```

**If subpackage tests fail with "Cannot find module" but root commands work, the subpackage needs its own symlink.** Start with the specific package you're working in; only broaden if needed.

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
| "Cannot find module X" | Missing symlink (root or per-package) | Symlink the relevant `node_modules` |
| `npm install` runs for minutes, lockfile conflicts | Ran install in worktree | Delete local `node_modules` + `package-lock.json`, symlink instead |
| Tests pass at root but fail in subpackage | Root symlink exists but subpackage symlink missing | Add per-package symlink |
| `ModuleNotFoundError` in Python | Missing `.venv` symlink | Symlink `.venv` from main repo |
| Turbo cache misses every run | Turbo hashes `node_modules` path | Symlink resolves this |
