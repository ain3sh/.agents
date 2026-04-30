#!/usr/bin/env python3
"""Repair a git worktree's dev environment from a healthy main: mirror node_modules,
mirror postinstall build outputs, rewire workspace symlinks, link venvs.

Defaults to the cwd worktree; WORKTREE_REPAIR_ALL=1 sweeps all worktrees.
See SKILL.md for env vars. Idempotent. Never installs in the worktree.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ALL = os.environ.get("WORKTREE_REPAIR_ALL") == "1"
WORKTREES_ROOT = os.environ.get("WORKTREES_ROOT", "").strip()
EXTRA_MIRROR_DIRS = [s.strip() for s in os.environ.get("WORKTREE_MIRROR_DIRS", "").split(",") if s.strip()]

_PKG_BUILD_RAW = os.environ.get("WORKTREE_PACKAGE_BUILD_DIRS")
if _PKG_BUILD_RAW is None:
    PACKAGE_BUILD_DIRS_OVERRIDE: list[str] | None = None  # auto-detect from package.json
else:
    PACKAGE_BUILD_DIRS_OVERRIDE = [s.strip() for s in _PKG_BUILD_RAW.split(",") if s.strip()]

CWD = Path.cwd().resolve()


def git_worktrees(start: Path) -> tuple[Path, list[Path]]:
    raw = subprocess.check_output(
        ["git", "worktree", "list", "--porcelain"], cwd=start, text=True
    )
    paths = [Path(l.split(" ", 1)[1]).resolve() for l in raw.splitlines() if l.startswith("worktree ")]
    if not paths:
        sys.exit("no git worktrees found")
    return paths[0], paths[1:]


def remove(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.exists():
        shutil.rmtree(path)


def find_sample_file(root: Path, max_depth: int = 2) -> Path | None:
    queue: list[tuple[Path, int]] = [(root, 0)]
    while queue:
        d, depth = queue.pop(0)
        try:
            entries = list(d.iterdir())
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
    rel = sample.relative_to(src)
    cand = dst / rel
    if not cand.is_file() or cand.is_symlink():
        return False
    return sample.stat().st_ino == cand.stat().st_ino


def mirror(src: Path, dst: Path) -> bool:
    if already_mirrored(src, dst):
        return False
    remove(dst)
    dst.mkdir(parents=True, exist_ok=True)
    subprocess.check_call(["cp", "-al", str(src) + "/.", str(dst) + "/"])
    return True


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
    changed = total = 0
    for name, rel in pkgs.items():
        target = wt / rel
        if not target.exists():
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


def discover_local_node_modules(main: Path) -> list[Path]:
    return sorted(
        p.relative_to(main)
        for p in main.glob("**/node_modules")
        if p.is_dir()
        and p != main / "node_modules"
        and ".git" not in p.parts
        and "node_modules" not in p.relative_to(main).parent.parts
    )


def link_venvs(main: Path, wt: Path) -> str:
    state: list[str] = []
    for env_name in (".venv", "venv"):
        src, dst = main / env_name, wt / env_name
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


def is_git_ignored(wt: Path, rel: str) -> bool:
    try:
        subprocess.check_call(
            ["git", "check-ignore", "-q", rel],
            cwd=wt, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def safe_mirror(src: Path, dst: Path, wt: Path, rel_for_check: str) -> str:
    """Hardlink-mirror src->dst with a safety guard. Returns a status string."""
    if not src.exists():
        return "src-missing"
    if not src.is_dir():
        return "src-not-dir"
    if not dst.parent.exists():
        return "wt-parent-missing"
    if dst.exists() and not is_git_ignored(wt, rel_for_check):
        return "dst-tracked-refusing"
    return "rebuilt" if mirror(src, dst) else "fresh"


def mirror_extras(main: Path, wt: Path) -> str:
    if not EXTRA_MIRROR_DIRS:
        return "none"
    parts: list[str] = []
    for rel in EXTRA_MIRROR_DIRS:
        rel_path = Path(rel)
        status = safe_mirror(main / rel_path, wt / rel_path, wt, rel)
        parts.append(f"{rel}:{status}")
    return " ".join(parts)


def _collect_export_strings(value) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        out: list[str] = []
        for v in value.values():
            out.extend(_collect_export_strings(v))
        return out
    if isinstance(value, list):
        out = []
        for v in value:
            out.extend(_collect_export_strings(v))
        return out
    return []


# Always source, never build output; filter to skip TS-as-source packages.
_SOURCE_DIRS = {"src", "source", "sources"}


def detect_package_build_dirs(pkg_root: Path) -> set[str]:
    """Infer build output dirs from a package.json's entry-point fields."""
    if PACKAGE_BUILD_DIRS_OVERRIDE is not None:
        return set(PACKAGE_BUILD_DIRS_OVERRIDE)
    try:
        pj = json.loads((pkg_root / "package.json").read_text())
    except Exception:
        return set()
    paths: list[str] = []
    for key in ("main", "module", "types", "browser", "unpkg", "jsdelivr"):
        v = pj.get(key)
        if isinstance(v, str):
            paths.append(v)
    paths.extend(_collect_export_strings(pj.get("exports")))
    dirs: set[str] = set()
    for p in paths:
        if p.startswith("./"):
            p = p[2:]
        elif p.startswith("/"):
            p = p[1:]
        if "/" not in p:
            continue
        d = p.split("/", 1)[0]
        if not d or d in _SOURCE_DIRS or d in {".", ".."} or any(c in d for c in "*?[]{}"):
            continue
        dirs.add(d)
    return dirs


def mirror_package_builds(main: Path, wt: Path, pkgs: dict[str, Path]) -> str:
    """Mirror per-package build output dirs (dist/, lib/, etc.) from main."""
    rebuilt = fresh = tracked = 0
    refused: list[str] = []
    for _name, rel in pkgs.items():
        wt_pkg = wt / rel
        # Use the worktree's package.json -- branch's build config may differ from main.
        for d in detect_package_build_dirs(wt_pkg):
            rel_dir = str(rel / d)
            status = safe_mirror(main / rel / d, wt / rel / d, wt, rel_dir)
            if status == "rebuilt":
                rebuilt += 1
            elif status == "fresh":
                fresh += 1
            elif status == "dst-tracked-refusing":
                tracked += 1
                refused.append(rel_dir)
            # src-missing / src-not-dir / wt-parent-missing: silently skip
    summary = f"rebuilt={rebuilt} fresh={fresh}"
    if tracked:
        summary += f" tracked-skip={tracked}"
        for r in refused:
            print(f"  refusing to clobber tracked path: {r}")
    return summary


def select_targets(others: list[Path]) -> list[Path]:
    if ALL:
        targets = others
        if WORKTREES_ROOT:
            root = Path(WORKTREES_ROOT).resolve()
            targets = [t for t in targets if t == root or root in t.parents]
        return targets
    match = next((p for p in others if CWD == p or p in CWD.parents), None)
    if match is None:
        print(
            f"cwd {CWD} is not inside a non-main worktree; "
            "set WORKTREE_REPAIR_ALL=1 to repair all worktrees"
        )
        return []
    return [match]


def main() -> None:
    main_repo, others = git_worktrees(CWD)
    targets = select_targets(others)
    if not targets:
        return

    main_local_nms = discover_local_node_modules(main_repo)

    for i, wt in enumerate(targets, 1):
        pkgs = workspaces(wt)
        root_built = mirror(main_repo / "node_modules", wt / "node_modules")
        root_changed, root_total = rewire(wt / "node_modules", wt, pkgs)

        local_built = local_fresh = local_changed = local_total = 0
        for rel_nm in main_local_nms:
            if not (wt / rel_nm.parent).exists():
                continue
            if mirror(main_repo / rel_nm, wt / rel_nm):
                local_built += 1
            else:
                local_fresh += 1
            c, t = rewire(wt / rel_nm, wt, pkgs)
            local_changed += c
            local_total += t

        pkg_builds = mirror_package_builds(main_repo, wt, pkgs)
        extras = mirror_extras(main_repo, wt)
        venv = link_venvs(main_repo, wt)

        print(
            f"[{i}/{len(targets)}] {wt.name}: "
            f"root={'rebuilt' if root_built else 'fresh'} ({root_changed}/{root_total} links); "
            f"local built={local_built} fresh={local_fresh} ({local_changed}/{local_total} links); "
            f"pkg_builds={pkg_builds}; extras={extras}; venv={venv}"
        )


if __name__ == "__main__":
    main()
