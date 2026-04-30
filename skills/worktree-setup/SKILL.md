---
name: worktree-setup
description: "Repair a git worktree's dev environment (mirror main's deps, rewire workspace symlinks, populate postinstall builds). Use when cwd is in a worktree and tooling fails to find modules, types, or build outputs."
---

# Worktree Setup

## Quickstart

Once per worktree, before invoking validators or other tooling:

```bash
python3 ~/.agents/skills/worktree-setup/scripts/repair.py        # repair this worktree
python3 ~/.agents/skills/worktree-setup/scripts/verify.py        # structural sanity check
```

Both default to the cwd worktree and are idempotent. `WORKTREE_REPAIR_ALL=1` / `WORKTREE_VERIFY_ALL=1` opt into a host-wide sweep.

## Detection

If the cwd path contains `worktree` (e.g. `myrepo-worktrees/feat-123`), you're in one. Explicit check:

```bash
MAIN_REPO=$(git worktree list | head -1 | awk '{print $1}')
WT_ROOT=$(git rev-parse --show-toplevel)
[ "$WT_ROOT" != "$MAIN_REPO" ] && echo "WORKTREE -- repair before tooling"
```

## Rules

- Don't run `npm install` / `bun install` / `pnpm install` or create a venv in a worktree -- the worktree links to main's instead.
- Workspace packages must resolve to the **current worktree**, via relative symlinks (so SSHFS and alternate mount paths still work).
- Workspace discovery reads the **worktree branch's** `package.json`, not main's.

## Repair

```bash
python3 ~/.agents/skills/worktree-setup/scripts/repair.py
```

Run from inside the worktree (or anywhere with `WORKTREE_REPAIR_ALL=1`). Main's dependencies and any generated artifacts must be healthy first (`npm install`, `npm run setup`, etc. -- in main only).

What it does, all idempotent:

- hardlink-mirrors root and package-local `node_modules` from main
- rewires workspace packages to the worktree's own `packages/`, with relative symlinks
- mirrors postinstall build outputs per workspace package (auto-detected from each `package.json`'s `main`/`module`/`types`/`exports` fields), so `packages/<pkg>/dist/` etc. populate without rebuilding
- links `.venv`/`venv` from main when present

Optional env vars:

| Var | Effect |
|---|---|
| `WORKTREE_REPAIR_ALL=1` | Repair every non-main worktree on the host. |
| `WORKTREES_ROOT=/path` | In all-mode, only repair worktrees under this dir. |
| `WORKTREE_MIRROR_DIRS=a,b/c` | Comma-separated repo-relative paths to additionally mirror from main (e.g. generated artifact dirs at the repo root). |
| `WORKTREE_PACKAGE_BUILD_DIRS=dist,lib` | Override the auto-detected per-package build output dirs. Set empty to disable build-output mirroring. |

**Never sweep silently** -- `WORKTREE_REPAIR_ALL=1` rebuilds every sibling worktree's `node_modules`. Other sessions may have a dev server, IDE indexer, or install holding files.

**Safety:** any mirror that would clobber an existing destination refuses unless the destination is git-ignored. A typo in `WORKTREE_MIRROR_DIRS` cannot wipe tracked source.

**Hardlink caveat:** mirrored build dirs are hardlinks to main. Tools that *unlink-and-rewrite* (most bundlers, tsc) break the link cleanly. Tools that modify files *in place* would cross-contaminate main; for those, set `WORKTREE_PACKAGE_BUILD_DIRS=` to disable build mirroring and rebuild fresh in the worktree.

Workspace discovery supports the npm/yarn/bun `"workspaces"` field in `package.json` (array form, or yarn-berry's `{"packages": [...]}`). pnpm-workspace.yaml, lerna, and non-JS managers are not handled.

## Verify

```bash
python3 ~/.agents/skills/worktree-setup/scripts/verify.py
```

Structural checks:

1. Workspace package entries in `node_modules` are symlinks, not real directories.
2. Those symlinks are relative.
3. Those symlinks resolve under the worktree.
4. Each workspace package's declared entry points (`main`, `module`, `types`, `exports`) actually exist (catches missing postinstall builds -- empty `dist/` etc.).
5. No other symlinks in the worktree point to absolute paths outside main + worktree boundaries.

Optional env vars:

| Var | Effect |
|---|---|
| `WORKTREE_VERIFY_ALL=1` | Verify every non-main worktree on the host. |
| `WORKTREES_ROOT=/path` | In all-mode, only verify worktrees under this dir. |
| `WORKTREE_SMOKE_CMD="..."` | Shell command run in each target's worktree root; non-zero exit fails verification. |

Exit code 0 if all targets pass, 1 otherwise.

## Path migration warning

After moving a repo or its worktrees between hosts/paths, fix `.git/worktrees/*/gitdir` and each worktree's `.git` pointer **before** `git worktree prune`. Prune unregisters valid worktrees if those pointers still reference the old path.

## Failure map

| Symptom | Fix |
|---|---|
| `Cannot find module X` from a workspace package | Run repair |
| Workspace package added on this branch but absent in main's `node_modules` | Run repair (discovery reads the worktree's `package.json`, so the link is created if the package directory exists in the worktree) |
| Stale exports, impossible type errors, or relative imports failing from a workspace package | Run repair |
| `Cannot find module '@scope/pkg/dist/...'` or workspace package's `dist/` is empty | Postinstall build not mirrored. Repair auto-detects build dirs from entry points; if your build dir isn't referenced there, set `WORKTREE_PACKAGE_BUILD_DIRS=...` and rerun |
| Verify reports a workspace entry point not found | Same -- rerun repair, or extend `WORKTREE_PACKAGE_BUILD_DIRS` |
| Missing files under a repo-root generated artifact dir | Add the path to `WORKTREE_MIRROR_DIRS` and rerun repair |
| Verify reports a workspace package is a real directory, not a symlink | An install materialized it -- `rm -rf` that path inside `node_modules` and rerun repair |
| Install was run inside the worktree | `rm -rf` the worktree's `node_modules` and rerun repair |
| Works locally, fails through SSHFS or an alternate mount path | Run repair (relative symlinks survive remount) |
| Sibling worktree also looks broken | Re-run with `WORKTREE_REPAIR_ALL=1` from a quiet shell |
| Valid worktrees disappeared after `git worktree prune` | Restore/fix `.git/worktrees/*/gitdir` and worktree `.git` pointer files |
