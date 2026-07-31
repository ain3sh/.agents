#!/usr/bin/env python3
"""Detach a worktree from dependencies and artifacts shared with its main repo.

Defaults to the cwd worktree; WORKTREE_BREAK_ALL=1 sweeps all non-main
worktrees. Removes mirrored node_modules and known mirrored artifact dirs,
unlinks symlinks into main, and copy-breaks any remaining hardlinks to main.
"""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

ALL = os.environ.get("WORKTREE_BREAK_ALL") == "1"
DRY_RUN = os.environ.get("WORKTREE_BREAK_DRY_RUN") == "1"
WORKTREES_ROOT = os.environ.get("WORKTREES_ROOT", "").strip()
EXTRA_MIRROR_DIRS = [
    value.strip()
    for value in os.environ.get("WORKTREE_MIRROR_DIRS", "").split(",")
    if value.strip()
]

_PKG_BUILD_RAW = os.environ.get("WORKTREE_PACKAGE_BUILD_DIRS")
if _PKG_BUILD_RAW is None:
    PACKAGE_BUILD_DIRS_OVERRIDE: list[str] | None = None
else:
    PACKAGE_BUILD_DIRS_OVERRIDE = [
        value.strip() for value in _PKG_BUILD_RAW.split(",") if value.strip()
    ]

CWD = Path.cwd().resolve()
_SOURCE_DIRS = {"src", "source", "sources"}


def git_worktrees(start: Path) -> tuple[Path, list[Path]]:
    raw = subprocess.check_output(
        ["git", "worktree", "list", "--porcelain"], cwd=start, text=True
    )
    paths = [
        Path(line.split(" ", 1)[1]).resolve()
        for line in raw.splitlines()
        if line.startswith("worktree ")
    ]
    if not paths:
        sys.exit("no git worktrees found")
    return paths[0], paths[1:]


def workspaces(root: Path) -> dict[str, Path]:
    try:
        raw = json.loads((root / "package.json").read_text()).get("workspaces", [])
    except Exception:
        return {}
    if isinstance(raw, dict):
        raw = raw.get("packages", [])
    if not isinstance(raw, list):
        return {}
    found: dict[str, Path] = {}
    for pattern in raw:
        if not isinstance(pattern, str):
            continue
        for pkg_json in sorted(root.glob(pattern + "/package.json")):
            try:
                name = json.loads(pkg_json.read_text()).get("name")
            except Exception:
                continue
            if isinstance(name, str) and name:
                found[name] = pkg_json.parent.relative_to(root)
    return found


def _collect_export_strings(value) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        out: list[str] = []
        for nested in value.values():
            out.extend(_collect_export_strings(nested))
        return out
    if isinstance(value, list):
        out = []
        for nested in value:
            out.extend(_collect_export_strings(nested))
        return out
    return []


def detect_package_build_dirs(pkg_root: Path) -> set[str]:
    if PACKAGE_BUILD_DIRS_OVERRIDE is not None:
        return set(PACKAGE_BUILD_DIRS_OVERRIDE)
    try:
        package = json.loads((pkg_root / "package.json").read_text())
    except Exception:
        return set()

    paths: list[str] = []
    for key in ("main", "module", "types", "browser", "unpkg", "jsdelivr"):
        value = package.get(key)
        if isinstance(value, str):
            paths.append(value)
    paths.extend(_collect_export_strings(package.get("exports")))

    dirs: set[str] = set()
    for value in paths:
        if value.startswith("./"):
            value = value[2:]
        elif value.startswith("/"):
            value = value[1:]
        if "/" not in value:
            continue
        directory = value.split("/", 1)[0]
        if (
            not directory
            or directory in _SOURCE_DIRS
            or directory in {".", ".."}
            or any(char in directory for char in "*?[]{}")
        ):
            continue
        dirs.add(directory)
    return dirs


def is_git_ignored(wt: Path, rel: Path) -> bool:
    return (
        subprocess.run(
            ["git", "check-ignore", "-q", str(rel)],
            cwd=wt,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        ).returncode
        == 0
    )


def safe_relative_path(raw: str) -> Path:
    path = Path(raw)
    if path.is_absolute() or ".." in path.parts:
        sys.exit(f"refusing unsafe mirror path: {raw}")
    return path


def find_node_modules(wt: Path) -> list[Path]:
    found: list[Path] = []
    for dirpath, dirnames, _filenames in os.walk(wt, followlinks=False):
        if ".git" in Path(dirpath).parts:
            dirnames[:] = []
            continue
        kept: list[str] = []
        for dirname in dirnames:
            path = Path(dirpath) / dirname
            if dirname == "node_modules":
                found.append(path)
            else:
                kept.append(dirname)
        dirnames[:] = kept
    return sorted(found)


def find_mirrored_dirs(wt: Path) -> list[Path]:
    candidates: set[Path] = set()
    for rel in workspaces(wt).values():
        for directory in detect_package_build_dirs(wt / rel):
            candidates.add(wt / rel / directory)
    for raw in EXTRA_MIRROR_DIRS:
        candidates.add(wt / safe_relative_path(raw))

    return sorted(
        path
        for path in candidates
        if (path.exists() or path.is_symlink())
        and is_git_ignored(wt, path.relative_to(wt))
    )


def directory_shares_files(src: Path, dst: Path) -> bool:
    if dst.is_symlink():
        try:
            return is_within(dst.resolve(strict=False), src)
        except (OSError, RuntimeError):
            return False
    if not src.is_dir() or not dst.is_dir():
        return False
    for dirpath, dirnames, filenames in os.walk(dst, followlinks=False):
        current = Path(dirpath)
        dirnames[:] = [name for name in dirnames if not (current / name).is_symlink()]
        for name in filenames:
            path = current / name
            if path.is_symlink():
                continue
            counterpart = src / path.relative_to(dst)
            try:
                metadata = path.stat()
                source_metadata = counterpart.stat()
            except OSError:
                continue
            if (
                metadata.st_dev == source_metadata.st_dev
                and metadata.st_ino == source_metadata.st_ino
            ):
                return True
    return False


def remove(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.exists():
        shutil.rmtree(path)


def is_within(path: Path, root: Path) -> bool:
    return path == root or root in path.parents


def excluded(path: Path, roots: list[Path]) -> bool:
    return any(is_within(path, root) for root in roots)


def find_main_symlinks(wt: Path, main_repo: Path, exclusions: list[Path]) -> list[Path]:
    found: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(wt, followlinks=False):
        current = Path(dirpath)
        if ".git" in current.parts or excluded(current, exclusions):
            dirnames[:] = []
            continue
        dirnames[:] = [
            name
            for name in dirnames
            if not excluded(current / name, exclusions)
        ]
        for name in dirnames + filenames:
            path = current / name
            if not path.is_symlink():
                continue
            try:
                target = path.resolve(strict=False)
            except (OSError, RuntimeError):
                continue
            if is_within(target, main_repo):
                found.append(path)
    return sorted(found)


def hardlink_candidates(wt: Path, exclusions: list[Path]) -> list[tuple[Path, int, int]]:
    found: list[tuple[Path, int, int]] = []
    for dirpath, dirnames, filenames in os.walk(wt, followlinks=False):
        current = Path(dirpath)
        if ".git" in current.parts or excluded(current, exclusions):
            dirnames[:] = []
            continue
        dirnames[:] = [
            name
            for name in dirnames
            if not excluded(current / name, exclusions)
        ]
        for name in filenames:
            path = current / name
            try:
                metadata = path.lstat()
            except OSError:
                continue
            if stat.S_ISREG(metadata.st_mode) and metadata.st_nlink > 1:
                found.append((path, metadata.st_dev, metadata.st_ino))
    return found


def main_inode_matches(
    main_repo: Path, candidate_keys: set[tuple[int, int]]
) -> set[tuple[int, int]]:
    if not candidate_keys:
        return set()
    found: set[tuple[int, int]] = set()
    for dirpath, dirnames, filenames in os.walk(main_repo, followlinks=False):
        if ".git" in Path(dirpath).parts:
            dirnames[:] = []
            continue
        for name in filenames:
            path = Path(dirpath) / name
            try:
                metadata = path.lstat()
            except OSError:
                continue
            key = (metadata.st_dev, metadata.st_ino)
            if key in candidate_keys:
                found.add(key)
                if found == candidate_keys:
                    return found
    return found


def copy_break_hardlink(path: Path) -> None:
    descriptor, temp_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.break-"
    )
    os.close(descriptor)
    temp = Path(temp_name)
    try:
        shutil.copy2(path, temp, follow_symlinks=False)
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def select_targets(others: list[Path]) -> list[Path]:
    if ALL:
        targets = others
        if WORKTREES_ROOT:
            root = Path(WORKTREES_ROOT).resolve()
            targets = [target for target in targets if is_within(target, root)]
        return targets
    match = next((path for path in others if is_within(CWD, path)), None)
    if match is None:
        print("cwd not inside a non-main worktree; nothing to break")
        return []
    return [match]


def break_worktree(main_repo: Path, wt: Path) -> None:
    node_modules = [
        path
        for path in find_node_modules(wt)
        if directory_shares_files(
            main_repo / path.relative_to(wt),
            path,
        )
    ]
    mirrored_dirs = [
        path
        for path in find_mirrored_dirs(wt)
        if directory_shares_files(
            main_repo / path.relative_to(wt),
            path,
        )
    ]
    removals = sorted(
        set(node_modules + mirrored_dirs), key=lambda path: len(path.parts)
    )

    if not DRY_RUN:
        for path in sorted(removals, key=lambda item: len(item.parts), reverse=True):
            remove(path)

    symlinks = find_main_symlinks(wt, main_repo, removals if DRY_RUN else [])
    if not DRY_RUN:
        for path in symlinks:
            path.unlink()

    candidates = hardlink_candidates(wt, removals if DRY_RUN else [])
    candidate_keys = {(device, inode) for _path, device, inode in candidates}
    shared_keys = main_inode_matches(main_repo, candidate_keys)
    hardlinks = [
        path for path, device, inode in candidates if (device, inode) in shared_keys
    ]
    if not DRY_RUN:
        for path in hardlinks:
            copy_break_hardlink(path)

    action = "would break" if DRY_RUN else "broken"
    print(
        f"{wt.name}: {action} "
        f"(node_modules={len(node_modules)}, mirrored_dirs={len(mirrored_dirs)}, "
        f"main_symlinks={len(symlinks)}, hardlinks={len(hardlinks)})"
    )


def main() -> None:
    main_repo, others = git_worktrees(CWD)
    targets = select_targets(others)
    for wt in targets:
        break_worktree(main_repo, wt)


if __name__ == "__main__":
    main()
