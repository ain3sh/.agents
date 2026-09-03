#!/usr/bin/env python3
"""Repair a git worktree's dev environment from a healthy source: mirror node_modules,
mirror postinstall build outputs, rewire workspace symlinks, link venvs.

Defaults to the cwd worktree and primary source; --from selects a registered
source worktree. WORKTREE_REPAIR_ALL=1 sweeps all worktrees.
See SKILL.md for env vars. Idempotent. Never installs in the worktree.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from collections import deque
from pathlib import Path

from _common import (
    CWD,
    EXTRA_MIRROR_DIRS,
    detect_package_build_dirs,
    ensure_disk_headroom,
    env_flag,
    find_node_modules,
    git_ignored_paths,
    git_tracked_paths,
    git_worktrees,
    parse_source_args,
    remove,
    repo_lock,
    select_source,
    select_targets,
    workspaces,
)

RSYNC = shutil.which("rsync")


# ============================================================================
# Hardlink mirroring
# ============================================================================


def find_sample_file(root: Path, max_depth: int = 2) -> Path | None:
    queue: deque[tuple[Path, int]] = deque([(root, 0)])
    while queue:
        directory, depth = queue.popleft()
        try:
            entries = list(directory.iterdir())
        except (FileNotFoundError, PermissionError):
            continue
        for entry in entries:
            if entry.is_file() and not entry.is_symlink():
                return entry
        if depth < max_depth:
            for entry in entries:
                if entry.is_dir() and not entry.is_symlink():
                    queue.append((entry, depth + 1))
    return None


def already_mirrored(src: Path, dst: Path) -> bool:
    if not dst.is_dir() or dst.is_symlink():
        return False
    try:
        src_names = {p.name for p in src.iterdir()}
        dst_names = {p.name for p in dst.iterdir()}
    except FileNotFoundError:
        return False
    if not src_names.issubset(dst_names):
        return False
    sample = find_sample_file(src)
    if sample is None:
        return True
    cand = dst / sample.relative_to(src)
    if not cand.is_file() or cand.is_symlink():
        return False
    return sample.stat().st_ino == cand.stat().st_ino


def mirror(src: Path, dst: Path, verbose: bool = False) -> bool:
    # Non-JS repos have no node_modules in the source; nothing to mirror.
    if not src.is_dir():
        return False
    if already_mirrored(src, dst):
        return False
    ensure_disk_headroom(dst)
    dst.mkdir(parents=True, exist_ok=True)
    if verbose:
        print(
            f"  rebuilding {dst} from source (interruptible; rerun resumes)",
            flush=True,
        )
    # rsnapshot-style converge-in-place: files unchanged vs the link-dest
    # become hardlinks to the source, deltas are fixed up, extras deleted. Unlike
    # rmtree + cp -al this is incremental (cost scales with what changed in
    # the source) and an interrupted run leaves a valid tree the rerun resumes.
    proc = subprocess.run(
        ["rsync", "-a", "--delete", f"--link-dest={src}/", f"{src}/", f"{dst}/"],
        check=False,
    )
    if proc.returncode == 24:
        print("  warning: source changed during mirror; rerun repair", file=sys.stderr)
    elif proc.returncode != 0:
        sys.exit(f"rsync failed with exit code {proc.returncode}")
    return True


def safe_mirror(src: Path, dst: Path, ignored: bool) -> str:
    """Hardlink-mirror src->dst with safety guards. Returns a status string."""
    if not src.exists():
        return "src-missing"
    if not src.is_dir():
        return "src-not-dir"
    if not dst.parent.exists():
        return "wt-parent-missing"
    if dst.exists() and not ignored:
        return "dst-tracked-refusing"
    return "rebuilt" if mirror(src, dst) else "fresh"


# ============================================================================
# Workspace symlinks
# ============================================================================


def rel_link(link: Path, target: Path) -> bool:
    desired = os.path.relpath(target, link.parent)
    if link.is_symlink() and os.readlink(link) == desired:
        return False
    if link.exists() or link.is_symlink():
        remove(link)
    link.parent.mkdir(parents=True, exist_ok=True)
    link.symlink_to(desired)
    return True


def rewire(nm: Path, wt: Path, pkgs: dict[str, Path]) -> tuple[int, int]:
    if not nm.exists():
        return 0, 0
    own_dir = nm.parent.resolve()
    changed = total = 0
    for name, rel in pkgs.items():
        target = wt / rel
        if not target.exists():
            continue
        # Self-reference slot: this workspace owns `nm`, so its name would link
        # to its own dir. Never create a `<pkg>/node_modules/<own-name>` self-link.
        # If a third-party dependency shares the workspace's name (e.g. an app
        # named "storybook" that also depends on the "storybook" package), the
        # real dependency lives in this slot and a self-link would clobber it.
        # Defer to whatever the node_modules mirror placed from the source.
        if target.resolve() == own_dir:
            continue
        if name.startswith("@"):
            scope, pkg = name.split("/", 1)
            scope_dir = nm / scope
            if scope_dir.is_symlink() or scope_dir.is_file():
                scope_dir.unlink()
            scope_dir.mkdir(parents=True, exist_ok=True)
            link = scope_dir / pkg
        else:
            link = nm / name
        total += 1
        if rel_link(link, target):
            changed += 1
    return changed, total


# ============================================================================
# Mirror groups
# ============================================================================


def discover_local_node_modules(source: Path) -> list[Path]:
    root_nm = source / "node_modules"
    return [p.relative_to(source) for p in find_node_modules(source) if p != root_nm]


def link_venvs(source: Path, wt: Path) -> str:
    state: list[str] = []
    for env_name in (".venv", "venv"):
        src, dst = source / env_name, wt / env_name
        if not src.exists():
            continue
        desired = os.path.relpath(src, dst.parent)
        if dst.is_symlink() and os.readlink(dst) == desired:
            state.append(f"{env_name}:fresh")
        else:
            remove(dst)
            dst.symlink_to(desired)
            state.append(f"{env_name}:linked")
    return ",".join(state) if state else "none"


def mirror_extras(source: Path, wt: Path) -> str:
    if not EXTRA_MIRROR_DIRS:
        return "none"
    ignored = git_ignored_paths(wt, EXTRA_MIRROR_DIRS)
    parts: list[str] = []
    for rel in EXTRA_MIRROR_DIRS:
        status = safe_mirror(source / rel, wt / rel, ignored=rel in ignored)
        parts.append(f"{rel}:{status}")
    return " ".join(parts)


def mirror_package_builds(source: Path, wt: Path, pkgs: dict[str, Path]) -> str:
    """Mirror per-package build output dirs (dist/, lib/, etc.) from source."""
    candidates: list[tuple[Path, Path, str]] = []
    for rel in pkgs.values():
        # Use the target's package.json -- its build config may differ from the source.
        candidates.extend(
            (rel, Path(d), str(rel / d)) for d in detect_package_build_dirs(wt / rel)
        )

    rel_dirs = [rel_dir for _rel, _build_dir, rel_dir in candidates]
    tracked = git_tracked_paths(wt, rel_dirs)
    ignored = git_ignored_paths(wt, rel_dirs)
    rebuilt = fresh = source_skips = 0
    for rel, build_dir, rel_dir in candidates:
        # Export maps may point at tracked trees outside a conventional src/
        # directory (for example packages/runtime/auth/src/index.ts). Treat any
        # tracked content conservatively: a mirror must never replace it.
        if rel_dir in tracked:
            source_skips += 1
            continue
        status = safe_mirror(
            source / rel / build_dir, wt / rel / build_dir, ignored=rel_dir in ignored
        )
        if status == "rebuilt":
            rebuilt += 1
        elif status == "fresh":
            fresh += 1
        # src-missing / src-not-dir / wt-parent-missing: silently skip
    summary = f"rebuilt={rebuilt} fresh={fresh}"
    if source_skips:
        summary += f" source-skip={source_skips}"
    return summary


# ============================================================================
# Entry point
# ============================================================================


def repair_worktree(source_repo: Path, wt: Path, source_local_nms: list[Path]) -> str:
    pkgs = workspaces(wt)
    root_built = mirror(source_repo / "node_modules", wt / "node_modules", verbose=True)
    root_changed, root_total = rewire(wt / "node_modules", wt, pkgs)

    local_built = local_fresh = local_changed = local_total = 0
    for rel_nm in source_local_nms:
        if not (wt / rel_nm.parent).exists():
            continue
        if mirror(source_repo / rel_nm, wt / rel_nm, verbose=True):
            local_built += 1
        else:
            local_fresh += 1
        changed, total = rewire(wt / rel_nm, wt, pkgs)
        local_changed += changed
        local_total += total

    pkg_builds = mirror_package_builds(source_repo, wt, pkgs)
    extras = mirror_extras(source_repo, wt)
    venv = link_venvs(source_repo, wt)

    return (
        f"root={'rebuilt' if root_built else 'fresh'} ({root_changed}/{root_total} links); "
        f"local built={local_built} fresh={local_fresh} ({local_changed}/{local_total} links); "
        f"pkg_builds={pkg_builds}; extras={extras}; venv={venv}"
    )


def main() -> None:
    if RSYNC is None:
        sys.exit("repair requires rsync (sudo pacman -S rsync)")
    source_arg = parse_source_args(__doc__ or "")
    primary, others = git_worktrees(CWD)
    source = select_source(CWD, primary, others, source_arg)
    targets = select_targets(
        others,
        sweep=env_flag("WORKTREE_REPAIR_ALL"),
        missing_msg=(
            f"cwd {CWD} is not inside a non-main worktree; "
            "set WORKTREE_REPAIR_ALL=1 to repair all worktrees"
        ),
    )
    if not targets:
        return
    if targets == [source]:
        sys.exit(f"source and target are the same worktree: {source}")
    targets = [target for target in targets if target != source]

    with repo_lock(primary):
        source_local_nms = discover_local_node_modules(source)
        for i, wt in enumerate(targets, 1):
            summary = repair_worktree(source, wt, source_local_nms)
            print(f"[{i}/{len(targets)}] {wt.name} <- {source.name}: {summary}")


if __name__ == "__main__":
    main()
