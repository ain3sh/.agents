---
name: disk-cleanup
description: Reclaim Linux home and /tmp disk space with bounded, repeatable cleanup scripts. Use when disks fill, /tmp balloons, caches/toolchains/containers accumulate, or cleanup must preserve Factory sessions, models, source data, and active temp files.
---

# Disk Cleanup

Treat cleanup as a bounded transaction: snapshot protected state, delete only
named regenerable classes, then prove protected entries survived.

## Act

Set the skill path once:

```bash
DISK_CLEANUP="$HOME/.agents/skills/disk-cleanup/scripts"
SNAPSHOT="$HOME/.local/state/disk-cleanup/before.json"
PROTECTED_MODEL="$HOME/factory/shield-runs/quant-v6/U2p1007-q4km.gguf"
```

| Goal | Command |
|---|---|
| Capture baseline; stop if a protected path is missing | `python3 "$DISK_CLEANUP/snapshot.py" --protect "$PROTECTED_MODEL" --hash-protected --output "$SNAPSHOT"` |
| Preview aggressive `/tmp` cleanup | `python3 "$DISK_CLEANUP/clean_tmp.py"` |
| Purge inactive `/tmp` entries | `python3 "$DISK_CLEANUP/clean_tmp.py" --apply` |
| Preview aggressive home cleanup | `python3 "$DISK_CLEANUP/clean_home.py" --protect "$PROTECTED_MODEL"` |
| Apply aggressive home cleanup | `python3 "$DISK_CLEANUP/clean_home.py" --protect "$PROTECTED_MODEL" --apply` |
| Opt down to caches only | Add `--profile caches`; this skips installed toolchains, extensions, Docker, and the pnpm store |
| Delete exact generated directories | `python3 "$DISK_CLEANUP/clean_home.py" --generated /absolute/project/node_modules --generated /absolute/project/target --protect "$PROTECTED_MODEL" --apply` |
| Verify disk and protected state | `python3 "$DISK_CLEANUP/snapshot.py" --compare "$SNAPSHOT"` |

Omit `--protect "$PROTECTED_MODEL"` only when that path is intentionally gone.
Add every other irreplaceable path with another `--protect`.

## Detect

```bash
df -h "$HOME" /tmp
```

Use this skill when either filesystem is under pressure. Start with `/tmp` and
the default aggressive profile. Opt down only when the user asks for a narrow
cache-only pass.

## Rules

1. Never run recursive `du`, `find`, or `lsof +D` over a large home/repository tree -- they can stall for minutes and still do no cleanup.
2. Never delete or prune `~/.factory/sessions` -- it is source data, not cache; the scripts hard-block overlap.
3. Never infer safety from a filename or apparent size -- pass irreplaceable paths through `--protect`, and stop when a required path is missing.
4. Never sweep project trees for `node_modules`, `target`, or build output -- pass each exact generated directory with `--generated`.
5. Never claim success from deletion output -- compare the snapshot and report `df` before/after.

## Failure map

| Symptom | Action |
|---|---|
| Protected path is missing before cleanup | Stop; locate or recover it. Read `references/safety.md`. |
| Scan runs longer than seconds | Cancel it; use the scripts' bounded targets. |
| `/tmp` deletion reports permission errors | Leave foreign/system entries; rerun as the owning user, not with broad `sudo rm`. |
| `/tmp` remains full | Inspect only the remaining direct children: `du -x -h --max-depth=1 /tmp 2>/dev/null \| sort -h \| tail -40`. |
| Home remains full after aggressive cleanup | Inspect one known top-level directory at a time; read `references/targets.md`. |
| Snapshot comparison reports missing sessions or changed protected files | Stop all cleanup and preserve the filesystem for recovery. |

## References

Load on demand; do not reabsorb into this file.

- `references/safety.md` -- protection invariants, active `/tmp` detection, Btrfs/reflink caveats, and failed approaches.
- `references/targets.md` -- exact cache/aggressive target classes, toolchain rules, extension retention, Docker behavior, and generated-path grammar.
