# Mechanics

What each command does internally, its env vars, and its safety properties.
All three scripts default to the cwd worktree and the primary source, are
idempotent, and honor the same arguments and env vars whether invoked as
`worktree-cli <cmd>` or
`python3 ~/.agents/skills/worktree-setup/scripts/<cmd>.py` (the CLI subcommands
run these scripts in the current environment).

## Repair

Preconditions: the selected source's dependencies and generated artifacts are
healthy. The primary worktree is the default; `--from <worktree>` selects a
registered source by path, directory name, or branch.

What it does:

- hardlink-mirrors root and package-local `node_modules` from the source via `rsync -a --delete --link-dest=<source>` (rsnapshot-style): cost scales with what changed in the source, not the tree size, and an interrupted run leaves a valid tree the rerun resumes -- no rmtree-first window that strands a partial mirror
- rewires workspace packages to the worktree's own `packages/`, with relative symlinks
- clones postinstall build outputs per workspace package (auto-detected from each `package.json`'s `main`/`module`/`types`/`exports` fields) with `cp -a --reflink=auto`, so `packages/<pkg>/dist/` etc. populate without rebuilding. Clones share disk blocks on CoW filesystems (btrfs, XFS) and degrade to a plain copy elsewhere. A clone is refreshed when its sample file's size or mtime differs from the source, or when any file in it is still hardlinked to the source, so trees from older hardlink repairs convert on the next run
- conservatively skips auto-detected directories that contain any tracked content (for example an export rooted at `auth/src/` rather than `src/`)
- links `.venv`/`venv` from the source when present
- serializes with break and other repair runs through an `flock` in the repo's git dir, so concurrent sessions queue instead of stampeding the filesystem
- before the first rebuild, refuses to run when the filesystem is btrfs with metadata >= `WORKTREE_MAX_METADATA_PCT`% full AND < `WORKTREE_MIN_UNALLOCATED_GIB` GiB unallocated -- btrfs stalls in transaction commit there instead of failing cleanly, so the gate fails fast with the balance command to run

| Var | Effect |
|---|---|
| `WORKTREE_REPAIR_ALL=1` | Repair every non-main worktree on the host. |
| `WORKTREES_ROOT=/path` | In all-mode, only repair worktrees under this dir. |
| `WORKTREE_MIRROR_DIRS=a,b/c` | Comma-separated repo-relative paths to additionally clone from the source (e.g. generated artifact dirs at the repo root). |
| `WORKTREE_PACKAGE_BUILD_DIRS=dist,lib` | Override the auto-detected per-package build output dirs. Set empty to disable build-output cloning. |
| `WORKTREE_MAX_METADATA_PCT=90` | btrfs metadata fullness (percent) at which rebuilds are refused. |
| `WORKTREE_MIN_UNALLOCATED_GIB=2` | Minimum unallocated btrfs space (GiB) required when metadata is past the fullness threshold. |

**Safety:** any clone that would clobber an existing destination refuses unless
the destination is git-ignored. A typo in `WORKTREE_MIRROR_DIRS` cannot wipe
tracked source.

**Why build outputs are cloned, not hardlinked:** worktrees rebuild them, and
common writers truncate and rewrite the existing inode rather than replacing the
file (tsc's `sys.writeFile`, `Bun.write`, Bun's external sourcemaps). Through a
hardlink, that write lands in the source and in every sibling sharing the inode.
`node_modules` stays hardlinked because a shared worktree never installs into
it; tools that patch dependencies in place still need `break` first.

**Workspace discovery scope:** the npm/yarn/bun `"workspaces"` field in
`package.json` (array form, or yarn-berry's `{"packages": [...]}`).
`pnpm-workspace.yaml`, lerna, and non-JS managers are not handled.

## Break

Deliberate detachment, not routine cleanup -- repair remains the default. Use
when sharing another worktree's environment would undermine the task: reproducing an
install/postinstall, package-manager, native-build, patching, or lockfile
issue; validating against a genuinely independent dependency tree; or running
in-place-mutating tooling.

What it does:

- removes root and package-local `node_modules` when they share files with any registered sibling
- removes ignored, auto-detected package build directories when they share files with any registered sibling (clones from repair share none and stay)
- removes symlinks that resolve into any registered sibling, including linked `.venv`/`venv`
- copy-breaks remaining sibling-shared hardlinks in place, preserving paths and contents
- takes the same repo-wide `flock` as repair, so the two never interleave

It does not install or rebuild. Afterward, run the repository's normal
install/setup flow with its required runtime and package-manager versions.

| Var | Effect |
|---|---|
| `WORKTREE_BREAK_ALL=1` | Break sharing for every non-main worktree on the host. |
| `WORKTREE_BREAK_DRY_RUN=1` | Report what would be detached without changing files. |
| `WORKTREES_ROOT=/path` | In all-mode, only process worktrees under this dir. |
| `WORKTREE_MIRROR_DIRS=a,b/c` | Also remove matching extra mirror dirs when they still share files with a registered sibling; use the same value supplied to repair. |
| `WORKTREE_PACKAGE_BUILD_DIRS=dist,lib` | Override auto-detected package build dirs, matching repair's override. |

## Verify

Structural checks, exit 0 pass / 1 fail:

1. Workspace package entries in `node_modules` are symlinks, not real directories (self-reference slots are skipped -- see `troubleshooting.md`).
2. Those symlinks are relative.
3. Those symlinks resolve under the worktree.
4. Each workspace package entry point that exists in the selected source also exists in the worktree (catches mirrorable postinstall builds that repair missed, without requiring runtime-generated app outputs).
5. Mirrored build dirs share no inodes with any registered sibling (catches hardlinked trees from older repairs).
6. No other symlinks in the worktree point to absolute paths outside source + worktree boundaries.

| Var | Effect |
|---|---|
| `WORKTREE_VERIFY_ALL=1` | Verify every non-main worktree on the host. |
| `WORKTREES_ROOT=/path` | In all-mode, only verify worktrees under this dir. |
| `WORKTREE_SMOKE_CMD="..."` | Shell command run in each target's worktree root; non-zero exit fails verification. |

## Sweep warning

`WORKTREE_*_ALL=1` operates on every sibling worktree: repair rebuilds their
`node_modules`, break removes their dependency trees. Other sessions may have a
dev server, IDE indexer, or install holding those files. Never sweep silently.
