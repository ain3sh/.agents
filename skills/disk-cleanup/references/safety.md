# Safety and failure lessons

## Invariants

1. `~/.factory/sessions` is user source data. It is never a cache target. The
   home cleaner hard-protects it even when no `--protect` flags are supplied.
2. Every irreplaceable model, VM image, dataset, or artifact goes through
   `--protect`. The baseline snapshot refuses a missing protected path by
   default; absence is an incident to investigate, not evidence that cleanup may
   continue.
3. Cleanup is two-phase: dry-run, then `--apply`. Snapshot comparison is the
   completion gate.
4. Project cleanup accepts only exact paths whose basename is a known generated
   directory. It never discovers and recursively sweeps project trees.
5. `/tmp` cleanup preserves direct children referenced by live process cwd,
   file descriptors, memory maps, or `/proc/net/unix` socket paths. It also
   preserves display/session socket patterns and foreign-owned entries by
   default.

## Why the scripts avoid broad scans

`du --max-depth=2` or `find` over a hundreds-of-gigabytes repository/worktree
tree can spend ten minutes traversing duplicated dependency trees. Recursive
`lsof +D /tmp` has the same pathology. Those commands delay the cleanup and
encourage cancellation before any space is reclaimed.

Use:

- `df` for the real filesystem result.
- One known top-level directory at a time when diagnosis is still needed.
- `/proc/<pid>/{cwd,fd,maps}` for active `/tmp` roots.
- Exact cache and generated targets for deletion.

## Btrfs and apparent size

On Btrfs, `du` reports apparent ownership of reflinked extents and can sum to
more than filesystem capacity. A 400 GiB directory on a 346 GiB filesystem is
not proof that deleting it will reclaim 400 GiB. Report reclaimed space from
`df` before/after, not from summed directory sizes.

Hardlinked worktree dependencies have a second hazard: deleting or modifying
files through one worktree can affect shared state. Delete an exact generated
directory only when its owning workflow allows reconstruction. For Factory
worktrees, load `worktree-setup` before repairing or reinstalling dependencies.

## Missing protected path

If the baseline says a protected file is missing:

1. Stop cleanup.
2. Check only likely parent directories and known alternate locations first.
3. Do not launch a whole-home scan under disk pressure.
4. If recovery may be required, minimize writes to the filesystem and use the
   appropriate filesystem recovery procedure.
5. Never report the file intact without locating and validating it.

## Permission failures

Root- or service-owned `/tmp` entries are intentionally skipped. Do not respond
with broad `sudo rm -rf /tmp/*`; that crosses ownership and process boundaries.
If a specific foreign entry is proven stale, remove that exact path through its
owner or an explicitly reviewed elevated command.
