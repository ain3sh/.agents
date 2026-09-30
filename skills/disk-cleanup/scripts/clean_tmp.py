#!/usr/bin/env python3
"""Preview or purge inactive direct children of /tmp without recursive lsof."""

from __future__ import annotations

import argparse
import fnmatch
import os
import shutil
import sys
import time
from pathlib import Path

SYSTEM_PATTERNS = (
    ".X11-unix",
    ".ICE-unix",
    ".XIM-unix",
    ".font-unix",
    ".Test-unix",
    "systemd-private-*",
    "plasmalogin-*",
)


def top_level(path: str, root: Path) -> str | None:
    clean = path.removesuffix(" (deleted)")
    if not clean.startswith(f"{root}/"):
        return None
    try:
        relative = Path(clean).relative_to(root)
    except ValueError:
        return None
    return relative.parts[0] if relative.parts else None


def active_roots(root: Path) -> tuple[set[str], int]:
    active: set[str] = set()
    processes = 0
    for proc in Path("/proc").iterdir():
        if not proc.name.isdigit():
            continue
        processes += 1
        links = [proc / "cwd"]
        try:
            links.extend((proc / "fd").iterdir())
        except OSError:
            pass
        for link in links:
            try:
                target = os.readlink(link)
            except OSError:
                continue
            if name := top_level(target, root):
                active.add(name)
        try:
            maps = (proc / "maps").read_text(errors="replace")
        except OSError:
            continue
        for line in maps.splitlines():
            parts = line.split(maxsplit=5)
            if len(parts) == 6 and (name := top_level(parts[5], root)):
                active.add(name)
    try:
        unix_sockets = Path("/proc/net/unix").read_text(errors="replace")
    except OSError:
        unix_sockets = ""
    for line in unix_sockets.splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 8 and (name := top_level(parts[-1], root)):
            active.add(name)
    return active, processes


def matches_system_path(name: str) -> bool:
    return any(fnmatch.fnmatch(name, pattern) for pattern in SYSTEM_PATTERNS)


def remove(path: Path) -> None:
    if path.is_symlink() or not path.is_dir():
        path.unlink()
    else:
        shutil.rmtree(path)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--tmp-root", default="/tmp")
    result.add_argument(
        "--protect", action="append", default=[], help="Retain a path's temporary container"
    )
    result.add_argument("--min-age-hours", type=float, default=0)
    result.add_argument("--include-foreign", action="store_true")
    result.add_argument("--apply", action="store_true")
    result.add_argument("--verbose", action="store_true")
    return result


def main() -> int:
    args = parser().parse_args()
    root = Path(args.tmp_root).resolve(strict=True)
    if not root.is_dir():
        sys.exit(f"not a directory: {root}")
    if root in {Path("/"), Path.home().resolve()}:
        sys.exit(f"refusing unsafe temporary root: {root}")

    missing = [raw for raw in args.protect if not Path(raw).expanduser().exists()]
    if missing:
        sys.exit("ERROR protected path missing: " + ", ".join(missing))

    active, processes = active_roots(root)
    home = Path.home()
    dsx_cache = os.environ.get("DSX_CACHE_DIR") or str(
        Path(os.environ.get("XDG_CACHE_HOME") or str(home / ".cache")) / "dsx"
    )
    protected: set[str] = set()
    for raw in (*args.protect, dsx_cache, os.environ.get("DSX_DB_PATH")):
        if not raw:
            continue
        path = Path(raw).expanduser()
        for location in (Path(os.path.abspath(path)), path.resolve()):
            if location == root or location in root.parents:
                protected.update(child.name for child in root.iterdir())
            elif name := top_level(str(location), root):
                protected.add(name)
    if args.apply and processes == 0:
        sys.exit("refusing apply: could not inspect /proc")

    cutoff = time.time() - args.min_age_hours * 3600
    candidates: list[Path] = []
    skipped_active = skipped_protected = skipped_system = 0
    skipped_foreign = skipped_young = 0
    uid = os.getuid()

    for path in root.iterdir():
        try:
            stat = path.lstat()
        except OSError:
            continue
        if path.name in active:
            skipped_active += 1
        elif path.name in protected:
            skipped_protected += 1
        elif matches_system_path(path.name):
            skipped_system += 1
        elif stat.st_uid != uid and not args.include_foreign:
            skipped_foreign += 1
        elif stat.st_mtime > cutoff:
            skipped_young += 1
        else:
            candidates.append(path)

    print(
        f"mode={'apply' if args.apply else 'dry-run'} "
        f"candidates={len(candidates)} active={skipped_active} "
        f"protected={skipped_protected} "
        f"system={skipped_system} foreign={skipped_foreign} "
        f"young={skipped_young}"
    )
    shown = candidates if args.verbose else candidates[:50]
    for path in shown:
        print(f"{'REMOVE' if args.apply else 'WOULD_REMOVE'} {path}")
    if len(candidates) > len(shown):
        print(f"... {len(candidates) - len(shown)} more")

    if not args.apply:
        return 0

    failed = 0
    for path in candidates:
        try:
            remove(path)
        except OSError as error:
            failed += 1
            print(f"SKIP {path}: {error}", file=sys.stderr)
    print(f"removed={len(candidates) - failed} failed={failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
