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
6. Inactivity is not disposability. Source patches, evidence, paused-session
   fixtures, and datasets remain protected even with no open process reference.
   Pass their exact paths through `--protect`; this retains their entire direct
   `/tmp` container, including when the named path is a symlink.

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

Unlinking one hardlink does not change the other links' file contents, but it
also cannot reclaim the shared data until the last link is removed. In-place
writes can modify every hardlinked view. Delete an exact generated directory
only when its owning workflow allows reconstruction, and never reinstall into
shared Factory worktrees. Load `worktree-setup` before their dependency cleanup
or repair. Allocation recovery belongs to `btrfs.md`.

## Missing protected path

If the baseline says a protected file is missing:

1. Stop cleanup.
2. Check likely parent directories and known alternate locations. Search dsx
   for that exact path and inspect the prior operator decision before asking
   again. A prior **explicit** intentional-removal decision permits dropping
   the stale protection; a move requires locating and protecting the new path.
3. Never treat absence alone as permission or use `--allow-missing-protected`
   to skip uncertainty. If history does not resolve it, ask the operator once.
   Do not launch a whole-home scan under disk pressure.
4. If disappearance is unexpected and recovery may be required, minimize
   writes and use the appropriate filesystem recovery procedure.
5. Never report the file intact without locating and validating it.

## Cleanup ownership and verification

Keep one deletion owner. When the operator starts worktree removal, stop your
own cleaners and reminder loops; do not regenerate targets or restart against
the changing inventory. A protected path disappearing during that handoff is a
reason to stop and reconcile scope, not suppress the safety check.

For generated worktree cleanup, record source status and diffs before deletion
and compare afterward. A timestamp or missing process reference alone does not
authorize deleting a worktree; select scope through `targets.md`.

`snapshot.py` records session entry names and protected path metadata; with
`--hash-protected` it hashes explicitly named files. Protecting a directory does
**not** hash or enumerate its descendants. Name individual irreplaceable files
when claiming content integrity, and distinguish that from directory survival.

## Permission failures

Root- or service-owned `/tmp` entries are intentionally skipped. Do not respond
with broad `sudo rm -rf /tmp/*`; that crosses ownership and process boundaries.
If a specific foreign entry is proven stale, remove that exact path through its
owner or an explicitly reviewed elevated command.

## Validate script changes

Run the isolated CLI protection suite; it never targets the real `/tmp` root:

```bash
~/.agents/scripts/run-check test --cwd "$HOME/.agents" -- python3 -m unittest discover -s skills/disk-cleanup/tests -p 'test_clean_*.py' -v
```
