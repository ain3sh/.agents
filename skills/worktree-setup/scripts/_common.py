"""Shared helpers for the worktree-setup scripts (repair.py, verify.py, break.py).

Sibling scripts import this via sys.path[0] (the scripts directory), so
`uv run --no-project python <script>` keeps working from any cwd.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from collections.abc import Iterator, Sequence
from pathlib import Path

CWD = Path.cwd().resolve()
WORKTREES_ROOT = os.environ.get("WORKTREES_ROOT", "").strip()

# Always source, never build output; filters TS-as-source packages.
SOURCE_DIRS = {"src", "source", "sources"}


# ============================================================================
# Environment
# ============================================================================


def env_flag(name: str) -> bool:
    return os.environ.get(name) == "1"


def safe_relative_path(raw: str) -> Path:
    path = Path(raw)
    if path.is_absolute() or ".." in path.parts:
        sys.exit(f"refusing unsafe mirror path: {raw}")
    return path


EXTRA_MIRROR_DIRS = [
    value.strip()
    for value in os.environ.get("WORKTREE_MIRROR_DIRS", "").split(",")
    if value.strip()
]
for _raw in EXTRA_MIRROR_DIRS:
    safe_relative_path(_raw)

# None means auto-detect from package.json; an empty list disables mirroring.
_PKG_BUILD_RAW = os.environ.get("WORKTREE_PACKAGE_BUILD_DIRS")
PACKAGE_BUILD_DIRS_OVERRIDE: list[str] | None = (
    None
    if _PKG_BUILD_RAW is None
    else [value.strip() for value in _PKG_BUILD_RAW.split(",") if value.strip()]
)


# ============================================================================
# Git
# ============================================================================


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


def git_ignored_paths(wt: Path, rels: Sequence[str]) -> set[str]:
    """The subset of rels that git ignores, via one check-ignore call."""
    if not rels:
        return set()
    proc = subprocess.run(
        ["git", "check-ignore", "-z", "--stdin"],
        cwd=wt,
        input="\0".join(rels),
        capture_output=True,
        text=True,
        check=False,
    )
    return {rel for rel in proc.stdout.split("\0") if rel}


def git_tracked_paths(wt: Path, rels: Sequence[str]) -> set[str]:
    """The subset of rels that are tracked files or ancestors of tracked files."""
    if not rels:
        return set()
    try:
        output = subprocess.check_output(
            ["git", "ls-files", "-z", "--", *rels],
            cwd=wt,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        return set()
    tracked: set[str] = set()
    for raw in output.split(b"\0"):
        if not raw:
            continue
        name = raw.decode()
        tracked.add(name)
        while (cut := name.rfind("/")) != -1:
            name = name[:cut]
            tracked.add(name)
    return {rel for rel in rels if rel in tracked}


def select_targets(others: list[Path], sweep: bool, missing_msg: str) -> list[Path]:
    if sweep:
        if WORKTREES_ROOT:
            root = Path(WORKTREES_ROOT).resolve()
            return [target for target in others if is_within(target, root)]
        return others
    match = next((path for path in others if is_within(CWD, path)), None)
    if match is None:
        print(missing_msg)
        return []
    return [match]


# ============================================================================
# package.json
# ============================================================================


def read_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def workspaces(root: Path) -> dict[str, Path]:
    raw = read_json(root / "package.json").get("workspaces", [])
    if isinstance(raw, dict):
        raw = raw.get("packages", [])
    if not isinstance(raw, list):
        return {}
    found: dict[str, Path] = {}
    for pattern in raw:
        if not isinstance(pattern, str):
            continue
        for pkg_json in sorted(root.glob(pattern + "/package.json")):
            name = read_json(pkg_json).get("name")
            if isinstance(name, str) and name:
                found[name] = pkg_json.parent.relative_to(root)
    return found


def collect_export_strings(value) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        value = list(value.values())
    if isinstance(value, list):
        out: list[str] = []
        for nested in value:
            out.extend(collect_export_strings(nested))
        return out
    return []


def detect_package_build_dirs(pkg_root: Path) -> set[str]:
    """Infer build output dirs from a package.json's entry-point fields."""
    if PACKAGE_BUILD_DIRS_OVERRIDE is not None:
        return set(PACKAGE_BUILD_DIRS_OVERRIDE)
    package = read_json(pkg_root / "package.json")
    paths: list[str] = []
    for key in ("main", "module", "types", "browser", "unpkg", "jsdelivr"):
        value = package.get(key)
        if isinstance(value, str):
            paths.append(value)
    paths.extend(collect_export_strings(package.get("exports")))

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
            or directory in SOURCE_DIRS
            or directory in {".", ".."}
            or any(char in directory for char in "*?[]{}")
        ):
            continue
        dirs.add(directory)
    return dirs


# ============================================================================
# Filesystem
# ============================================================================


def remove(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.exists():
        shutil.rmtree(path)


def is_within(path: Path, root: Path) -> bool:
    return path == root or root in path.parents


def iter_tree(root: Path, exclusions: Sequence[Path] = ()) -> Iterator[os.DirEntry]:
    """Depth-first DirEntry stream under root, pruning .git and excluded subtrees.

    DirEntry type/symlink checks come from the scandir dirent, so filtering on
    them costs no extra stat calls (unlike os.walk + Path.is_symlink per entry).
    """
    excluded = {str(path) for path in exclusions}
    stack = [str(root)]
    while stack:
        current = stack.pop()
        try:
            entries = list(os.scandir(current))
        except OSError:
            continue
        for entry in entries:
            if entry.path in excluded:
                continue
            yield entry
            if entry.is_dir(follow_symlinks=False) and entry.name != ".git":
                stack.append(entry.path)


def find_node_modules(root: Path) -> list[Path]:
    """Every node_modules dir under root, without descending into .git or the
    found node_modules themselves (glob-based discovery walked all of them)."""
    found: list[Path] = []
    stack = [str(root)]
    while stack:
        current = stack.pop()
        try:
            entries = list(os.scandir(current))
        except OSError:
            continue
        for entry in entries:
            if entry.name == ".git":
                continue
            if entry.name == "node_modules" and entry.is_dir():
                found.append(Path(entry.path))
            elif entry.is_dir(follow_symlinks=False):
                stack.append(entry.path)
    return sorted(found)
