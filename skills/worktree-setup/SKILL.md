---
name: worktree-setup
description: Git worktree environment setup. Use when the working directory is a git worktree, when node_modules is missing or npm install fails, or when the user mentions worktrees. Prevents the common failure of running npm install in a worktree.
---

# Worktree Setup

## Detection

You are in a worktree if:
```bash
[ "$(git rev-parse --show-toplevel)" != "$(git worktree list | head -1 | awk '{print $1}')" ]
```

## Rule: Never `npm install` in a Worktree

Worktrees share the `.git` directory with the main repo but have their own working tree. Running `npm install` in a worktree is **always wrong** -- it's slow, creates lockfile conflicts, and duplicates hundreds of MB of dependencies.

Instead, **symlink `node_modules`** from the main repo:

```bash
if [ ! -d "node_modules" ] && [ ! -L "node_modules" ]; then
  MAIN_REPO=$(git worktree list | head -1 | awk '{print $1}')
  ln -s "$MAIN_REPO/node_modules" node_modules
fi
```

Run this **before** any tooling (lint, test, build, typecheck, dev server, etc.).

## Common Failure Modes

- **"Cannot find module X"** -- `node_modules` symlink is missing. Create it.
- **`npm install` runs for minutes then fails with lockfile conflicts** -- you ran install in a worktree. Delete the local `node_modules` and `package-lock.json` it created, then symlink instead.
- **Turbo cache misses on every run** -- turbo hashes `node_modules` path. Symlink resolves this.

## Worktree-Friendly Commands

All standard commands (`npm run lint`, `npm test`, `turbo run build`, etc.) work normally once the symlink is in place. No other worktree-specific adjustments are needed.
