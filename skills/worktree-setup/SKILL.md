---
name: worktree-setup
description: "Manage a git worktree's dev environment: mirror a healthy source worktree's dependencies and artifacts, or deliberately detach them for an independent install/repro. Use when worktree tooling cannot find modules/build outputs or when shared state would invalidate a clean environment test."
---

# Worktree Setup

Non-main worktrees share a healthy source worktree's dependencies through hardlink mirrors and relative symlinks -- never install into them. The primary worktree is the default source; `--from <worktree>` selects a registered sibling by path, directory name, or branch. Worktrees created by `worktree-cli new` (shell alias `gwk`) use the invoking worktree as their source (`--no-setup` skips).

## Act

| Goal | Command |
|---|---|
| Fix a broken or fresh worktree env | `worktree-cli repair [--from <worktree>]` |
| Structural sanity check (exit 1 = findings) | `worktree-cli verify [--from <worktree>]` |
| Repair, then verify | `worktree-cli setup [--from <worktree>]` |
| Independent env for install/repro work | `worktree-cli break`, then the repo's normal install flow |

Run from inside the worktree. All idempotent, cwd-scoped by default. Without `worktree-cli`, invoke the same scripts directly: `python3 ~/.agents/skills/worktree-setup/scripts/{repair,verify,break}.py`. `WORKTREE_*` env vars tune scope and mirror sets for both forms -- see `references/mechanics.md`.

After repair, Bun-driven packages only: run `bun run setup` / `bun run generate` from the package dir when `package.json` declares them. Never substitute install commands.

## Detect

You are in a worktree when `git rev-parse --show-toplevel` differs from the first path in `git worktree list`. A path containing `worktree` (e.g. `myrepo-worktrees/feat-123`) is a strong hint.

## Rules

1. **Never** run `npm/bun/pnpm install` or create a venv in a shared worktree -- writes can cross hardlinks into its source. Need independence? `worktree-cli break` first.
2. Workspace packages must resolve into the **current worktree** via **relative** symlinks (survives SSHFS and alternate mounts).
3. The selected source must be healthy first (installed + built); repair copies from it, never builds.
4. Never sweep (`WORKTREE_*_ALL=1`) silently -- sibling worktrees may be held by other sessions' dev servers, indexers, or installs.

## Failure map

| Symptom | Action |
|---|---|
| `Cannot find module X` from a workspace package | `worktree-cli repair` |
| repair refuses: "btrfs metadata is ... full" / rebuilds stall with ENOSPC | free space, then `sudo btrfs balance start -dusage=25 /`, rerun repair |
| Stale exports, impossible type errors, relative imports failing | `worktree-cli repair` |
| Workspace package added on this branch, absent in the default source | `worktree-cli repair --from <healthy-sibling>` (discovery reads the target's `package.json`) |
| `dist/` empty or `Cannot find module '@scope/pkg/dist/...'` | repair; if the build dir isn't auto-detected, set `WORKTREE_PACKAGE_BUILD_DIRS=...` and rerun |
| Missing repo-root generated artifact dir | add to `WORKTREE_MIRROR_DIRS`, rerun repair |
| verify: real directory where a symlink is expected | `rm -rf` that `node_modules` entry, rerun repair -- unless it is a self-reference slot: `references/troubleshooting.md` |
| Dangling `node_modules/.bin/<tool>` where tool name equals a workspace name | name collision: `references/troubleshooting.md` |
| Install was run inside the worktree | `rm -rf` its `node_modules`, rerun repair |
| Works locally, fails over SSHFS / alternate mount | `worktree-cli repair` |
| Sibling worktrees also broken | sweep with `WORKTREE_REPAIR_ALL=1` -- read the sweep warning in `references/mechanics.md` first |
| Tool mutates build outputs in place (would contaminate the source) | `WORKTREE_PACKAGE_BUILD_DIRS=` (empty) + rebuild fresh: `references/mechanics.md` |
| Worktrees vanished after `git worktree prune` | path migration: `references/troubleshooting.md` |

## References

Load on demand; do not reabsorb into this file.

- `references/mechanics.md` -- what repair/break/verify each do internally, all env vars, safety guards, hardlink caveats, workspace-discovery scope.
- `references/troubleshooting.md` -- extended walkthroughs: self-reference slots and name collisions, path migration after moving repos, choosing break vs repair.
