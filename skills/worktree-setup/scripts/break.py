#!/usr/bin/env python3
"""Detach a worktree from dependencies and artifacts shared with its main repo.

Defaults to the cwd worktree; WORKTREE_BREAK_ALL=1 sweeps all non-main
worktrees. Removes mirrored node_modules and known mirrored artifact dirs,
unlinks symlinks into main, and copy-breaks any remaining hardlinks to main.
"""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

from _common import (
    CWD,
    EXTRA_MIRROR_DIRS,
    detect_package_build_dirs,
    env_flag,
    find_node_modules,
    git_ignored_paths,
    git_worktrees,
    is_within,
    iter_tree,
    remove,
    repo_lock,
    select_targets,
    workspaces,
)

DRY_RUN = env_flag("WORKTREE_BREAK_DRY_RUN")


# ============================================================================
# Discovery
# ============================================================================


def find_mirrored_dirs(wt: Path) -> list[Path]:
    candidates: set[Path] = set()
    for rel in workspaces(wt).values():
        for directory in detect_package_build_dirs(wt / rel):
            candidates.add(wt / rel / directory)
    for raw in EXTRA_MIRROR_DIRS:
        candidates.add(wt / raw)

    present = sorted(path for path in candidates if path.exists() or path.is_symlink())
    rels = [str(path.relative_to(wt)) for path in present]
    ignored = git_ignored_paths(wt, rels)
    return [path for path, rel in zip(present, rels) if rel in ignored]


def directory_shares_files(src: Path, dst: Path) -> bool:
    if dst.is_symlink():
        try:
            return is_within(dst.resolve(strict=False), src)
        except (OSError, RuntimeError):
            return False
    if not src.is_dir() or not dst.is_dir():
        return False
    for entry in iter_tree(dst):
        if not entry.is_file(follow_symlinks=False):
            continue
        path = Path(entry.path)
        counterpart = src / path.relative_to(dst)
        try:
            metadata = entry.stat(follow_symlinks=False)
            source_metadata = counterpart.stat()
        except OSError:
            continue
        if (
            metadata.st_dev == source_metadata.st_dev
            and metadata.st_ino == source_metadata.st_ino
        ):
            return True
    return False


def scan_links(
    wt: Path, main_repo: Path, exclusions: list[Path]
) -> tuple[list[Path], list[tuple[Path, int, int]]]:
    """One walk collecting symlinks into main and multi-link file candidates."""
    symlinks: list[Path] = []
    hardlinks: list[tuple[Path, int, int]] = []
    for entry in iter_tree(wt, exclusions):
        if entry.is_symlink():
            path = Path(entry.path)
            try:
                target = path.resolve(strict=False)
            except (OSError, RuntimeError):
                continue
            if is_within(target, main_repo):
                symlinks.append(path)
        elif entry.is_file(follow_symlinks=False):
            try:
                metadata = entry.stat(follow_symlinks=False)
            except OSError:
                continue
            if metadata.st_nlink > 1:
                hardlinks.append((Path(entry.path), metadata.st_dev, metadata.st_ino))
    return sorted(symlinks), hardlinks


def main_inode_matches(
    main_repo: Path, candidate_keys: set[tuple[int, int]]
) -> set[tuple[int, int]]:
    if not candidate_keys:
        return set()
    found: set[tuple[int, int]] = set()
    for entry in iter_tree(main_repo):
        if not entry.is_file(follow_symlinks=False):
            continue
        try:
            metadata = entry.stat(follow_symlinks=False)
        except OSError:
            continue
        key = (metadata.st_dev, metadata.st_ino)
        if key in candidate_keys:
            found.add(key)
            if found == candidate_keys:
                return found
    return found


# ============================================================================
# Breaking
# ============================================================================


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


def break_worktree(main_repo: Path, wt: Path) -> None:
    node_modules = [
        path
        for path in find_node_modules(wt)
        if directory_shares_files(main_repo / path.relative_to(wt), path)
    ]
    mirrored_dirs = [
        path
        for path in find_mirrored_dirs(wt)
        if directory_shares_files(main_repo / path.relative_to(wt), path)
    ]
    removals = sorted(
        set(node_modules + mirrored_dirs), key=lambda path: len(path.parts)
    )

    if not DRY_RUN:
        for path in sorted(removals, key=lambda item: len(item.parts), reverse=True):
            remove(path)

    symlinks, candidates = scan_links(wt, main_repo, removals if DRY_RUN else [])
    if not DRY_RUN:
        for path in symlinks:
            path.unlink()

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
    targets = select_targets(
        others,
        sweep=env_flag("WORKTREE_BREAK_ALL"),
        missing_msg="cwd not inside a non-main worktree; nothing to break",
    )
    with repo_lock(main_repo):
        for wt in targets:
            break_worktree(main_repo, wt)


if __name__ == "__main__":
    main()
