#!/usr/bin/env python3
"""Capture or compare a bounded disk-cleanup safety snapshot."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any


def expanded(raw: str) -> Path:
    return Path(raw).expanduser().resolve(strict=False)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def disk_state(path: Path) -> dict[str, int | str]:
    usage = shutil.disk_usage(path)
    return {
        "path": str(path),
        "total": usage.total,
        "used": usage.used,
        "free": usage.free,
    }


def protected_state(path: Path, hash_file: bool) -> dict[str, Any]:
    state: dict[str, Any] = {"path": str(path), "exists": path.exists()}
    if not state["exists"]:
        return state
    stat = path.stat()
    state.update(
        {
            "size": stat.st_size,
            "inode": stat.st_ino,
            "mtime_ns": stat.st_mtime_ns,
            "kind": "dir" if path.is_dir() else "file",
        }
    )
    if hash_file and path.is_file():
        state["sha256"] = sha256(path)
    return state


def session_names(path: Path) -> list[str]:
    if not path.is_dir():
        return []
    return sorted(entry.name for entry in path.iterdir())


def capture(
    home: Path,
    tmp: Path,
    protected: list[Path],
    hash_protected: bool,
) -> dict[str, Any]:
    sessions = home / ".factory" / "sessions"
    return {
        "version": 1,
        "home": str(home),
        "tmp": str(tmp),
        "disks": [disk_state(home), disk_state(tmp)],
        "factory_sessions": {
            "path": str(sessions),
            "exists": sessions.is_dir(),
            "entries": session_names(sessions),
        },
        "protected": [protected_state(path, hash_protected) for path in protected],
    }


def print_summary(state: dict[str, Any]) -> None:
    for disk in state["disks"]:
        gib = disk["free"] / (1024**3)
        print(f"{disk['path']}: free={gib:.1f} GiB")
    sessions = state["factory_sessions"]
    print(
        f"{sessions['path']}: "
        f"exists={sessions['exists']} entries={len(sessions['entries'])}"
    )
    for item in state["protected"]:
        suffix = f" size={item['size']}" if item["exists"] else ""
        print(f"{item['path']}: exists={item['exists']}{suffix}")


def compare(before: dict[str, Any], after: dict[str, Any]) -> list[str]:
    findings: list[str] = []
    before_sessions = before["factory_sessions"]
    after_sessions = after["factory_sessions"]
    if before_sessions["exists"] and not after_sessions["exists"]:
        findings.append("Factory sessions directory disappeared")
    missing_sessions = sorted(
        set(before_sessions["entries"]) - set(after_sessions["entries"])
    )
    if missing_sessions:
        sample = ", ".join(missing_sessions[:10])
        findings.append(
            f"{len(missing_sessions)} Factory session entries disappeared: {sample}"
        )

    after_by_path = {item["path"]: item for item in after["protected"]}
    for old in before["protected"]:
        new = after_by_path.get(old["path"], {"exists": False})
        if old["exists"] and not new["exists"]:
            findings.append(f"protected path disappeared: {old['path']}")
            continue
        if not old["exists"]:
            continue
        for key in ("size", "inode", "sha256"):
            if key in old and old.get(key) != new.get(key):
                findings.append(
                    f"protected path changed {key}: {old['path']} "
                    f"({old.get(key)} -> {new.get(key)})"
                )
    return findings


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--home", default=str(Path.home()))
    result.add_argument("--tmp", default="/tmp")
    result.add_argument("--protect", action="append", default=[])
    result.add_argument("--hash-protected", action="store_true")
    result.add_argument("--allow-missing-protected", action="store_true")
    result.add_argument("--output", type=Path)
    result.add_argument("--compare", type=Path)
    return result


def main() -> int:
    args = parser().parse_args()
    home = expanded(args.home)
    tmp = expanded(args.tmp)

    before: dict[str, Any] | None = None
    protected = [expanded(raw) for raw in args.protect]
    hash_protected = args.hash_protected
    if args.compare:
        before = json.loads(args.compare.expanduser().read_text())
        if not protected:
            protected = [expanded(item["path"]) for item in before.get("protected", [])]
        hash_protected = hash_protected or any(
            "sha256" in item for item in before.get("protected", [])
        )

    state = capture(home, tmp, protected, hash_protected)
    print_summary(state)

    missing = [item["path"] for item in state["protected"] if not item["exists"]]
    if missing and not args.allow_missing_protected:
        for path in missing:
            print(f"ERROR protected path missing: {path}", file=sys.stderr)
        return 2

    if before is not None:
        findings = compare(before, state)
        if findings:
            for finding in findings:
                print(f"ERROR {finding}", file=sys.stderr)
            return 1
        print("verification=ok")

    if args.output:
        output = args.output.expanduser()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(state, indent=2) + "\n")
        print(f"snapshot={output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
