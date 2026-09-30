# Btrfs pressure and allocation recovery

## Diagnose once

```bash
df -h "$HOME" /tmp
btrfs filesystem usage "$HOME"
journalctl -k --since "20 minutes ago" --no-pager | rg -i 'btrfs|enospc'
```

`df` free space, unallocated device space, and metadata occupancy are different
resources. A filesystem can have tens of GiB free inside data chunks and still
fail allocation or relocation with ENOSPC. Kernel balance messages may confirm
failure without identifying the exhausted reservation; do not invent that
detail from aggregate percentages.

Use the actual Btrfs mount, not a hardcoded `/`. Obtain elevated diagnostics
from the operator when needed; if `sudo -n` requires a password, supply one
bounded command and wait for its output rather than retrying authentication.

## Reclaim before relocation

When unallocated space is near zero and metadata is under pressure, first
remove approved bulk regenerable data/worktrees (`targets.md`). Let the owning
removal finish and re-read allocation. Repeated small cache deletions and
balance threshold guesses are not substitutes for reclaiming headroom.

Deleting snapshots is a separate scope decision. Inspect dates, important
flags, and retention through the owning snapshot tool; do not delete rollback
points or alter retention without authorization.

## Bounded data-only balance

An empty-data-chunk pass requires no data relocation:

```bash
sudo btrfs balance start -dusage=0 /home &&
sudo btrfs filesystem usage /home
```

Zero chunks relocated means no eligible chunks, not progress. Do not walk
through 10%, 25%, 50%, and higher thresholds as a retry ladder. After substantial
reclaim, select one threshold from current occupancy or verified prior evidence
and limit the work, for example:

```bash
sudo btrfs balance start -dusage=90,limit=4 /home &&
sudo btrfs filesystem usage /home
```

This moves at most four qualifying data block groups; it does not balance
metadata or change profiles. It may release chunks, but success and the amount
reclaimed must come from the resulting allocation report.

| Result | Next action |
|---|---|
| Zero eligible chunks | Reassess occupancy and bulk reclaim; do not repeat the same filter. |
| Relocation ENOSPC | Stop balancing, inspect kernel/allocation evidence, and reclaim substantially more capacity before any new attempt. |
| Useful unallocated headroom and metadata pressure relieved | Stop balancing and retry the interrupted owning workflow. |

Never run a full balance, metadata balance, or profile conversion as a disk
cleanup fallback. Do not add an opaque loop-device filesystem member to escape
ENOSPC. These expand the risk beyond bounded reclaim.

## Evidence and stop condition

Session `9b7ef42d` (2026-09-30): at about 90% metadata and 1 MiB unallocated,
0%/25% data filters found no chunks and `dusage=90,limit=2` failed with ENOSPC.
After operator-owned bulk worktree removal, free space reached 51.8 GiB and
metadata fell to 72%; `dusage=90,limit=4` then relocated four chunks and released
2 GiB unallocated. This is evidence for **bulk reclaim before balance**, not a
universal 90% threshold or permission to remove those worktrees elsewhere.

Stop when the interrupted tool's actual allocation requirements are satisfied
and protected-state verification passes. In this incident, 51.8 GiB free,
72% metadata, and 2 GiB unallocated were sufficient to recommend retrying setup.
Do not keep deleting or balancing to optimize a cosmetic percentage.
