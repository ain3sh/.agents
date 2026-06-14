#!/usr/bin/env python3
"""Verify a worktree's dev environment: workspace symlinks, package entry points,
no stale absolute symlinks. See SKILL.md for env vars and the full check list.
Defaults to the cwd worktree; WORKTREE_VERIFY_ALL=1 sweeps all. Exit 0 ok, 1 fail.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ALL = os.environ.get("WORKTREE_VERIFY_ALL") == "1"
WORKTREES_ROOT = os.environ.get("WORKTREES_ROOT", "").strip()
SMOKE_CMD = os.environ.get("WORKTREE_SMOKE_CMD", "").strip()
CWD = Path.cwd().resolve()


def git_worktrees(start: Path) -> tuple[Path, list[Path]]:
    raw = subprocess.check_output(
        ["git", "worktree", "list", "--porcelain"], cwd=start, text=True
    )
    paths = [Path(l.split(" ", 1)[1]).resolve() for l in raw.splitlines() if l.startswith("worktree ")]
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


def package_link(nm: Path, name: str) -> Path:
    if name.startswith("@"):
        scope, pkg = name.split("/", 1)
        return nm / scope / pkg
    return nm / name


def all_node_modules(wt: Path) -> list[Path]:
    out = []
    if (wt / "node_modules").is_dir():
        out.append(wt / "node_modules")
    for p in wt.glob("**/node_modules"):
        if not p.is_dir() or p == wt / "node_modules":
            continue
        if ".git" in p.parts or "node_modules" in p.relative_to(wt).parent.parts:
            continue
        out.append(p)
    return sorted(out)


def check_workspace_links(wt: Path, pkgs: dict[str, Path]) -> list[tuple[str, str]]:
    findings: list[tuple[str, str]] = []
    for nm in all_node_modules(wt):
        for name in pkgs:
            link = package_link(nm, name)
            # Self-reference slot (see repair.py rewire): when a workspace owns
            # this node_modules, the slot named after it may legitimately hold a
            # real third-party dependency of the same name (or be absent), so it
            # is not a broken workspace link.
            if (wt / pkgs[name]).resolve() == nm.parent.resolve():
                continue
            if not link.exists() and not link.is_symlink():
                continue
            if not link.is_symlink():
                findings.append((
                    "error",
                    f"{link.relative_to(wt)} should be a symlink to the worktree's package but is a real directory "
                    "(probably installed in-place; remove it and rerun repair)",
                ))
                continue
            target = os.readlink(link)
            if os.path.isabs(target):
                findings.append(("error", f"{link.relative_to(wt)} is an absolute symlink ({target})"))
                continue
            real = os.path.realpath(link)
            if real != str(wt) and not real.startswith(str(wt) + os.sep):
                findings.append(("error", f"{link.relative_to(wt)} resolves outside the worktree -> {real}"))
    return findings


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


def check_package_entry_points(wt: Path, pkgs: dict[str, Path]) -> list[tuple[str, str]]:
    findings: list[tuple[str, str]] = []
    for name, rel in pkgs.items():
        pkg_root = wt / rel
        try:
            pj = json.loads((pkg_root / "package.json").read_text())
        except Exception:
            continue
        entries: list[tuple[str, str]] = []
        for key in ("main", "module", "types", "browser"):
            v = pj.get(key)
            if isinstance(v, str):
                entries.append((key, v))
        for v in _collect_export_strings(pj.get("exports")):
            entries.append(("exports", v))
        for key, raw in entries:
            cleaned = raw
            if cleaned.startswith("./"):
                cleaned = cleaned[2:]
            elif cleaned.startswith("/"):
                cleaned = cleaned[1:]
            if not cleaned or any(c in cleaned for c in "*?["):
                continue
            target = pkg_root / cleaned
            if not target.exists():
                findings.append((
                    "error",
                    f"workspace package {name}: {key}={raw} not found at "
                    f"{target.relative_to(wt)} (probably a postinstall build dir not "
                    "mirrored; rerun repair)",
                ))
    return findings


def find_stale_absolute_symlinks(scan_root: Path, allowed_roots: list[str]):
    for dirpath, dirnames, filenames in os.walk(scan_root, followlinks=False):
        parts = Path(dirpath).parts
        if ".git" in parts:
            dirnames[:] = []
            continue
        for name in dirnames + filenames:
            p = Path(dirpath) / name
            try:
                if not p.is_symlink():
                    continue
                target = os.readlink(p)
            except (OSError, ValueError):
                continue
            if not os.path.isabs(target):
                continue
            if any(target == r or target.startswith(r + os.sep) for r in allowed_roots):
                continue
            yield p, target


def run_smoke(wt: Path) -> tuple[bool, str]:
    if not SMOKE_CMD:
        return True, "skipped"
    try:
        subprocess.check_output(
            ["sh", "-c", SMOKE_CMD],
            cwd=wt, stderr=subprocess.STDOUT, timeout=120, text=True,
        )
        return True, "ok"
    except subprocess.CalledProcessError as e:
        return False, f"fail: {e.output[-300:].strip()}"
    except subprocess.TimeoutExpired:
        return False, "timeout"


def select_targets(others: list[Path]) -> list[Path]:
    if ALL:
        targets = others
        if WORKTREES_ROOT:
            root = Path(WORKTREES_ROOT).resolve()
            targets = [t for t in targets if t == root or root in t.parents]
        return targets
    match = next((p for p in others if CWD == p or p in CWD.parents), None)
    if match is None:
        print("cwd not inside a non-main worktree; nothing to verify")
        return []
    return [match]


def main() -> int:
    main_repo, others = git_worktrees(CWD)
    targets = select_targets(others)
    if not targets:
        return 0

    fail = 0
    for wt in targets:
        pkgs = workspaces(wt)
        link_findings = check_workspace_links(wt, pkgs)
        entry_findings = check_package_entry_points(wt, pkgs)
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
        if not ok:
            fail += 1

    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
