#!/usr/bin/env python3
"""Verify a worktree's dev environment: workspace symlinks, package entry points,
no stale absolute symlinks. See SKILL.md for env vars and the full check list.
Defaults to the cwd worktree; WORKTREE_VERIFY_ALL=1 sweeps all. Exit 0 ok, 1 fail.
"""

from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path

from _common import (
    CWD,
    collect_export_strings,
    env_flag,
    find_node_modules,
    git_worktrees,
    iter_tree,
    read_json,
    select_targets,
    workspaces,
)

SMOKE_CMD = os.environ.get("WORKTREE_SMOKE_CMD", "").strip()

Finding = tuple[str, str]


# ============================================================================
# Checks
# ============================================================================


def package_link(nm: Path, name: str) -> Path:
    if name.startswith("@"):
        scope, pkg = name.split("/", 1)
        return nm / scope / pkg
    return nm / name


def check_workspace_links(wt: Path, pkgs: dict[str, Path]) -> list[Finding]:
    findings: list[Finding] = []
    pkg_dirs = {name: (wt / rel).resolve() for name, rel in pkgs.items()}
    for nm in find_node_modules(wt):
        own_dir = nm.parent.resolve()
        for name in pkgs:
            # Self-reference slot (see repair.py rewire): when a workspace owns
            # this node_modules, the slot named after it may legitimately hold a
            # real third-party dependency of the same name (or be absent), so it
            # is not a broken workspace link.
            if pkg_dirs[name] == own_dir:
                continue
            link = package_link(nm, name)
            if not link.is_symlink():
                if link.exists():
                    findings.append(
                        (
                            "error",
                            f"{link.relative_to(wt)} should be a symlink to the "
                            "worktree's package but is a real directory (probably "
                            "installed in-place; remove it and rerun repair)",
                        )
                    )
                continue
            target = os.readlink(link)
            if os.path.isabs(target):
                findings.append(
                    (
                        "error",
                        f"{link.relative_to(wt)} is an absolute symlink ({target})",
                    )
                )
                continue
            real = os.path.realpath(link)
            if real != str(wt) and not real.startswith(str(wt) + os.sep):
                findings.append(
                    (
                        "error",
                        f"{link.relative_to(wt)} resolves outside the worktree -> {real}",
                    )
                )
    return findings


def check_package_entry_points(
    main_repo: Path, wt: Path, pkgs: dict[str, Path]
) -> list[Finding]:
    findings: list[Finding] = []
    for name, rel in pkgs.items():
        pkg_root = wt / rel
        pj = read_json(pkg_root / "package.json")
        if not pj:
            continue
        entries: list[tuple[str, str]] = [
            (key, value)
            for key in ("main", "module", "types", "browser")
            if isinstance(value := pj.get(key), str)
        ]
        entries.extend(
            ("exports", v) for v in collect_export_strings(pj.get("exports"))
        )
        for key, raw in entries:
            cleaned = raw
            if cleaned.startswith("./"):
                cleaned = cleaned[2:]
            elif cleaned.startswith("/"):
                cleaned = cleaned[1:]
            if not cleaned or any(char in cleaned for char in "*?["):
                continue
            target = pkg_root / cleaned
            main_target = main_repo / rel / cleaned
            if main_target.exists() and not target.exists():
                findings.append(
                    (
                        "error",
                        f"workspace package {name}: {key}={raw} not found at "
                        f"{target.relative_to(wt)} although main has "
                        f"{main_target.relative_to(main_repo)} (postinstall build dir was "
                        "not mirrored; rerun repair)",
                    )
                )
    return findings


def find_stale_absolute_symlinks(
    scan_root: Path, allowed_roots: list[str]
) -> Iterator[tuple[Path, str]]:
    for entry in iter_tree(scan_root):
        if not entry.is_symlink():
            continue
        try:
            target = os.readlink(entry.path)
        except OSError:
            continue
        if not os.path.isabs(target):
            continue
        if any(target == r or target.startswith(r + os.sep) for r in allowed_roots):
            continue
        yield Path(entry.path), target


def run_smoke(wt: Path) -> tuple[bool, str]:
    if not SMOKE_CMD:
        return True, "skipped"
    try:
        subprocess.check_output(
            ["sh", "-c", SMOKE_CMD],
            cwd=wt,
            stderr=subprocess.STDOUT,
            timeout=120,
            text=True,
        )
        return True, "ok"
    except subprocess.CalledProcessError as e:
        return False, f"fail: {e.output[-300:].strip()}"
    except subprocess.TimeoutExpired:
        return False, "timeout"


# ============================================================================
# Entry point
# ============================================================================


def verify_worktree(main_repo: Path, wt: Path) -> bool:
    pkgs = workspaces(wt)
    link_findings = check_workspace_links(wt, pkgs)
    entry_findings = check_package_entry_points(main_repo, wt, pkgs)
    stale = list(find_stale_absolute_symlinks(wt, [str(wt), str(main_repo)]))
    smoke_ok, smoke_msg = run_smoke(wt)

    ok = not link_findings and not entry_findings and not stale and smoke_ok
    print(
        f"{wt.name}: {'ok' if ok else 'FAIL'} "
        f"(workspace_findings={len(link_findings)}, "
        f"entry_findings={len(entry_findings)}, "
        f"stale_abs={len(stale)}, smoke={smoke_msg})"
    )
    for severity, msg in link_findings + entry_findings:
        print(f"  {severity}: {msg}")
    for path, target in stale:
        try:
            rel = path.relative_to(wt)
        except ValueError:
            rel = path
        print(f"  stale: {rel} -> {target}")
    return ok


def main() -> int:
    main_repo, others = git_worktrees(CWD)
    targets = select_targets(
        others,
        sweep=env_flag("WORKTREE_VERIFY_ALL"),
        missing_msg="cwd not inside a non-main worktree; nothing to verify",
    )
    fail = sum(1 for wt in targets if not verify_worktree(main_repo, wt))
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
