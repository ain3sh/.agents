# Mechanics

What each command does internally, its env vars, and its safety properties.
All three scripts default to the cwd worktree, are idempotent, and honor the
same env vars whether invoked as `worktree-cli <cmd>` or
`python3 ~/.agents/skills/worktree-setup/scripts/<cmd>.py` (the CLI subcommands
run these scripts in the current environment).

## Repair

Preconditions: main's dependencies and generated artifacts are healthy
(`npm install`, `npm run setup`, etc. -- run in **main only**).

What it does:

- hardlink-mirrors root and package-local `node_modules` from main
- rewires workspace packages to the worktree's own `packages/`, with relative symlinks
- mirrors postinstall build outputs per workspace package (auto-detected from each `package.json`'s `main`/`module`/`types`/`exports` fields), so `packages/<pkg>/dist/` etc. populate without rebuilding
- conservatively skips auto-detected directories that contain any tracked content (for example an export rooted at `auth/src/` rather than `src/`)
- links `.venv`/`venv` from main when present

| Var | Effect |
|---|---|
| `WORKTREE_REPAIR_ALL=1` | Repair every non-main worktree on the host. |
| `WORKTREES_ROOT=/path` | In all-mode, only repair worktrees under this dir. |
| `WORKTREE_MIRROR_DIRS=a,b/c` | Comma-separated repo-relative paths to additionally mirror from main (e.g. generated artifact dirs at the repo root). |
| `WORKTREE_PACKAGE_BUILD_DIRS=dist,lib` | Override the auto-detected per-package build output dirs. Set empty to disable build-output mirroring. |

**Safety:** any mirror that would clobber an existing destination refuses unless
the destination is git-ignored. A typo in `WORKTREE_MIRROR_DIRS` cannot wipe
tracked source.

**Hardlink caveat:** mirrored build dirs are hardlinks to main. Tools that
*unlink-and-rewrite* (most bundlers, tsc) break the link cleanly. Tools that
modify files *in place* would cross-contaminate main; for those, set
`WORKTREE_PACKAGE_BUILD_DIRS=` (empty) to disable build mirroring and rebuild
fresh in the worktree.

**Workspace discovery scope:** the npm/yarn/bun `"workspaces"` field in
`package.json` (array form, or yarn-berry's `{"packages": [...]}`).
`pnpm-workspace.yaml`, lerna, and non-JS managers are not handled.

## Break

Deliberate detachment, not routine cleanup -- repair remains the default. Use
when sharing main's environment would undermine the task: reproducing an
install/postinstall, package-manager, native-build, patching, or lockfile
issue; validating against a genuinely independent dependency tree; or running
in-place-mutating tooling.

What it does:

- removes root and package-local `node_modules` only when they actually share files with main
- removes ignored, auto-detected package build directories when they share files with main
- removes symlinks that resolve into main, including linked `.venv`/`venv`
- copy-breaks any remaining hardlinks to main in place, preserving paths and contents

It does not install or rebuild. Afterward, run the repository's normal
install/setup flow with its required runtime and package-manager versions.

| Var | Effect |
|---|---|
| `WORKTREE_BREAK_ALL=1` | Break sharing for every non-main worktree on the host. |
| `WORKTREE_BREAK_DRY_RUN=1` | Report what would be detached without changing files. |
| `WORKTREES_ROOT=/path` | In all-mode, only process worktrees under this dir. |
| `WORKTREE_MIRROR_DIRS=a,b/c` | Also remove matching extra mirror dirs when they still share files with main; use the same value supplied to repair. |
| `WORKTREE_PACKAGE_BUILD_DIRS=dist,lib` | Override auto-detected package build dirs, matching repair's override. |

## Verify

Structural checks, exit 0 pass / 1 fail:

1. Workspace package entries in `node_modules` are symlinks, not real directories (self-reference slots are skipped -- see `troubleshooting.md`).
2. Those symlinks are relative.
3. Those symlinks resolve under the worktree.
4. Each workspace package entry point that exists in main also exists in the worktree (catches mirrorable postinstall builds that repair missed, without requiring runtime-generated app outputs).
5. No other symlinks in the worktree point to absolute paths outside main + worktree boundaries.

| Var | Effect |
|---|---|
| `WORKTREE_VERIFY_ALL=1` | Verify every non-main worktree on the host. |
| `WORKTREES_ROOT=/path` | In all-mode, only verify worktrees under this dir. |
| `WORKTREE_SMOKE_CMD="..."` | Shell command run in each target's worktree root; non-zero exit fails verification. |

## Sweep warning

`WORKTREE_*_ALL=1` operates on every sibling worktree: repair rebuilds their
`node_modules`, break removes their dependency trees. Other sessions may have a
dev server, IDE indexer, or install holding those files. Never sweep silently.
