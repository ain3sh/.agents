# Troubleshooting

Extended walkthroughs for the failure-map rows that need more than one command.

## Self-reference slots and name collisions

A workspace package whose name also matches a real third-party dependency
(e.g. an app literally named `storybook` that also depends on the `storybook`
npm package) keeps the **real dependency** in its own `node_modules/<name>`
slot. Repair and verify treat that self-reference slot specially: they never
overwrite it with a self-link, and verify does not flag it as a broken
workspace link. It still needs **no install** -- the mirror from main supplies
the real package.

Symptom of a historical clobber: `<app>/node_modules/.bin/<tool>` is a dangling
symlink, or `spawn ... ENOENT` for a tool whose name equals a workspace package
name. An older repair replaced the real package with a `<name> -> ..`
self-link. Fix:

1. Rerun repair -- current repair leaves self-reference slots to the mirror.
2. If the bad self-link persists: `rm <app>/node_modules/<name>`, rerun repair
   to restore the real package from main.
3. If main's copy is also missing, build it in **main** first, then repair.

## Path migration (moved repo or worktrees)

After moving a repo or its worktrees between hosts or paths, fix
`.git/worktrees/*/gitdir` and each worktree's `.git` pointer file **before**
running `git worktree prune`. Prune unregisters valid worktrees whose pointers
still reference the old path. If worktrees already vanished after a prune,
restore those pointer files and re-register.

Relative workspace symlinks survive path moves and SSHFS/alternate mounts by
design; a repair after migration fixes anything that didn't.

## Break vs repair

Repair is the fast default: shared, disposable, no installs. Break is a
one-way door into an independent environment -- after it, the worktree needs
the repository's full install/setup flow, with the repo's required runtime and
package-manager versions. Reach for break only when sharing itself is the
problem: install/postinstall/lockfile repros, native builds, patching
dependencies, or tools that mutate mirrored files in place. Preview with
`WORKTREE_BREAK_DRY_RUN=1`.

## Sibling worktrees also broken

Re-run with the relevant `WORKTREE_*_ALL=1` from a quiet shell -- but read the
sweep warning in `mechanics.md` first: sweeps touch worktrees other sessions
may be using.
