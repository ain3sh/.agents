#!/usr/bin/env python3
"""Detach a worktree from dependencies and artifacts shared with any sibling.

Defaults to the cwd worktree; WORKTREE_BREAK_ALL=1 sweeps all non-main
worktrees. Removes mirrored node_modules and known mirrored artifact dirs,
unlinks symlinks into registered siblings, and copy-breaks remaining shared
hardlinks.
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


def shared_with_source(path: Path, wt: Path, source_repos: list[Path]) -> bool:
    try:
        metadata = path.stat(follow_symlinks=False)
    except OSError:
        return False
    for source in source_repos:
        counterpart = source / path.relative_to(wt)
        try:
            source_metadata = counterpart.stat()
        except OSError:
            continue
        if (
            metadata.st_dev == source_metadata.st_dev
            and metadata.st_ino == source_metadata.st_ino
        ):
            return True
    return False


def directory_shares_files(source_repos: list[Path], wt: Path, directory: Path) -> bool:
    if directory.is_symlink():
        try:
            target = directory.resolve(strict=False)
        except (OSError, RuntimeError):
            return False
        return any(is_within(target, source) for source in source_repos)
    if not directory.is_dir():
        return False
    for entry in iter_tree(directory):
        if not entry.is_file(follow_symlinks=False):
            continue
        if shared_with_source(Path(entry.path), wt, source_repos):
            return True
    return False


def scan_links(
    wt: Path, source_repos: list[Path], exclusions: list[Path]
) -> tuple[list[Path], list[Path]]:
    """Collect symlinks into siblings and multi-link file candidates."""
    symlinks: list[Path] = []
    hardlinks: list[Path] = []
    for entry in iter_tree(wt, exclusions):
        if entry.is_symlink():
            path = Path(entry.path)
            try:
                target = path.resolve(strict=False)
            except (OSError, RuntimeError):
                continue
            if any(is_within(target, source) for source in source_repos):
                symlinks.append(path)
        elif entry.is_file(follow_symlinks=False):
            try:
                metadata = entry.stat(follow_symlinks=False)
            except OSError:
                continue
            if metadata.st_nlink > 1:
                hardlinks.append(Path(entry.path))
    return sorted(symlinks), hardlinks


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


def break_worktree(source_repos: list[Path], wt: Path) -> None:
    node_modules = [
        path
        for path in find_node_modules(wt)
        if directory_shares_files(source_repos, wt, path)
    ]
    mirrored_dirs = [
        path
        for path in find_mirrored_dirs(wt)
        if directory_shares_files(source_repos, wt, path)
    ]
    removals = sorted(
        set(node_modules + mirrored_dirs), key=lambda path: len(path.parts)
    )

    if not DRY_RUN:
        for path in sorted(removals, key=lambda item: len(item.parts), reverse=True):
            remove(path)

    symlinks, candidates = scan_links(wt, source_repos, removals if DRY_RUN else [])
    if not DRY_RUN:
        for path in symlinks:
            path.unlink()

    hardlinks = [
        path for path in candidates if shared_with_source(path, wt, source_repos)
    ]
    if not DRY_RUN:
        for path in hardlinks:
            copy_break_hardlink(path)

    action = "would break" if DRY_RUN else "broken"
    print(
        f"{wt.name}: {action} "
        f"(node_modules={len(node_modules)}, mirrored_dirs={len(mirrored_dirs)}, "
        f"source_symlinks={len(symlinks)}, hardlinks={len(hardlinks)})"
    )


def main() -> None:
    primary, others = git_worktrees(CWD)
    targets = select_targets(
        others,
        sweep=env_flag("WORKTREE_BREAK_ALL"),
        missing_msg="cwd not inside a non-main worktree; nothing to break",
    )
    all_worktrees = [primary, *others]
    with repo_lock(primary):
        for wt in targets:
            sources = [source for source in all_worktrees if source != wt]
            break_worktree(sources, wt)


if __name__ == "__main__":
    main()
