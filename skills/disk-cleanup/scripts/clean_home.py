#!/usr/bin/env python3
"""Preview or apply bounded home-directory cleanup."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

CACHE_TARGETS = (
    ".local/share/baloo",
    ".config/Factory/Cache",
    ".config/Factory/Code Cache",
    ".config/Factory (DEV)/Cache",
    ".config/Factory (DEV)/Code Cache",
    ".config/Code/Cache",
    ".config/Code/Code Cache",
    ".config/Code/CachedData",
    ".config/Code/CachedExtensionVSIXs",
    ".config/Electron/Cache",
    ".config/Electron/Code Cache",
    ".config/gcloud/logs",
    ".factory/logs",
    ".factory/snapshots",
    ".factory/plugins/cache",
    ".cargo/registry",
    ".cargo/git",
    ".bun/install/cache",
    ".nvm/.cache",
    ".npm/_cacache",
    ".local/share/Trash",
)
AGGRESSIVE_TARGETS = (".local/share/pnpm/store",)
CLEAR_CONTENTS = (".cache", ".factory/logs", ".factory/snapshots")
GENERATED_NAMES = {
    ".next",
    ".pytest_cache",
    ".ruff_cache",
    ".turbo",
    ".venv",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "target",
}


def expanded(raw: str) -> Path:
    return Path(raw).expanduser().resolve(strict=False)


def overlaps(left: Path, right: Path) -> bool:
    return left == right or left in right.parents or right in left.parents


def assert_safe(target: Path, home: Path, protected: list[Path]) -> None:
    if target == home or home not in target.parents:
        sys.exit(f"refusing path outside home or equal to home: {target}")
    for path in protected:
        if overlaps(target, path):
            sys.exit(f"refusing target overlapping protected path: {target} <> {path}")


def remove(path: Path, clear_contents: bool) -> None:
    if clear_contents:
        for child in list(path.iterdir()):
            if child.is_symlink() or not child.is_dir():
                child.unlink()
            else:
                shutil.rmtree(child)
    elif path.is_symlink() or not path.is_dir():
        path.unlink()
    else:
        shutil.rmtree(path)


def version_key(name: str) -> tuple[int, ...]:
    numbers = re.findall(r"\d+", name)
    return tuple(int(number) for number in numbers)


def current_node_toolchain(root: Path) -> str | None:
    node = shutil.which("node")
    if node:
        resolved = Path(node).resolve(strict=False)
        try:
            relative = resolved.relative_to(root)
            if relative.parts:
                return relative.parts[0]
        except ValueError:
            pass
    versions = [path.name for path in root.iterdir() if path.is_dir()]
    return max(versions, key=version_key) if versions else None


def current_rust_toolchain() -> str | None:
    if shutil.which("rustup") is None:
        return None
    result = subprocess.run(
        ["rustup", "show", "active-toolchain"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        check=False,
    )
    return result.stdout.split()[0] if result.returncode == 0 else None


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--home", default=str(Path.home()))
    result.add_argument(
        "--profile",
        choices=("caches", "aggressive"),
        default="aggressive",
        help="aggressive is the default; caches opts down",
    )
    result.add_argument("--protect", action="append", default=[])
    result.add_argument("--allow-missing-protected", action="store_true")
    result.add_argument("--generated", action="append", default=[])
    result.add_argument(
        "--prune-toolchains",
        action=argparse.BooleanOptionalAction,
        default=None,
    )
    result.add_argument(
        "--prune-vscode-extensions",
        action=argparse.BooleanOptionalAction,
        default=None,
    )
    result.add_argument("--keep-vscode-extension", action="append", default=[])
    result.add_argument(
        "--drop-all-vscode-extensions",
        action="store_true",
        help="do not retain the default rust-analyzer extension",
    )
    result.add_argument(
        "--prune-docker",
        action=argparse.BooleanOptionalAction,
        default=None,
    )
    result.add_argument("--apply", action="store_true")
    return result


def main() -> int:
    args = parser().parse_args()
    home = expanded(args.home)
    aggressive = args.profile == "aggressive"
    prune_toolchains = (
        aggressive if args.prune_toolchains is None else args.prune_toolchains
    )
    prune_vscode_extensions = (
        aggressive
        if args.prune_vscode_extensions is None
        else args.prune_vscode_extensions
    )
    prune_docker = aggressive if args.prune_docker is None else args.prune_docker
    keep_extensions = list(args.keep_vscode_extension)
    if aggressive and not args.drop_all_vscode_extensions:
        keep_extensions.append("rust-lang.rust-analyzer-")
    sessions = home / ".factory" / "sessions"
    protected = [sessions, *(expanded(raw) for raw in args.protect)]
    missing = [path for path in protected[1:] if not path.exists()]
    if missing and not args.allow_missing_protected:
        for path in missing:
            print(f"ERROR protected path missing: {path}", file=sys.stderr)
        return 2

    targets: list[tuple[Path, bool, str]] = [(home / ".cache", True, "cache contents")]
    targets.extend(
        (
            home / relative,
            relative in CLEAR_CONTENTS,
            "cache/log/trash",
        )
        for relative in CACHE_TARGETS
    )
    if args.profile == "aggressive":
        targets.extend(
            (home / relative, False, "aggressive package store")
            for relative in AGGRESSIVE_TARGETS
        )

    for raw in args.generated:
        path = expanded(raw)
        if path.name not in GENERATED_NAMES:
            sys.exit(
                f"refusing generated path with unapproved basename {path.name!r}: "
                f"{path}"
            )
        targets.append((path, False, "explicit generated path"))

    if prune_toolchains:
        node_root = home / ".nvm" / "versions" / "node"
        if node_root.is_dir():
            keep = current_node_toolchain(node_root)
            print(f"KEEP node toolchain {keep}")
            targets.extend(
                (path, False, "inactive Node toolchain")
                for path in node_root.iterdir()
                if path.is_dir() and path.name != keep
            )
        rust_root = home / ".rustup" / "toolchains"
        if rust_root.is_dir():
            keep = current_rust_toolchain()
            if keep is None:
                print("SKIP Rust toolchains: active toolchain unknown", file=sys.stderr)
            else:
                print(f"KEEP rust toolchain {keep}")
                targets.extend(
                    (path, False, "inactive Rust toolchain")
                    for path in rust_root.iterdir()
                    if path.is_dir() and path.name != keep
                )

    if prune_vscode_extensions:
        extension_root = home / ".vscode" / "extensions"
        if extension_root.is_dir():
            targets.extend(
                (path, False, "reinstallable VS Code extension")
                for path in extension_root.iterdir()
                if path.is_dir()
                and not any(path.name.startswith(prefix) for prefix in keep_extensions)
            )

    existing: list[tuple[Path, bool, str]] = []
    seen: set[Path] = set()
    for target, clear_contents, reason in targets:
        target = target.resolve(strict=False)
        assert_safe(target, home, protected)
        if target.exists() and target not in seen:
            seen.add(target)
            existing.append((target, clear_contents, reason))

    print(
        f"mode={'apply' if args.apply else 'dry-run'} "
        f"profile={args.profile} targets={len(existing)}"
    )
    for target, _, reason in existing:
        print(f"{'REMOVE' if args.apply else 'WOULD_REMOVE'} {target} [{reason}]")

    if args.apply:
        for target, clear_contents, _ in existing:
            remove(target, clear_contents)

    docker_failed = False
    if prune_docker:
        docker = shutil.which("docker")
        if docker is None:
            print("SKIP Docker: executable not found", file=sys.stderr)
        elif args.apply:
            result = subprocess.run(
                [docker, "system", "prune", "-af", "--volumes"],
                check=False,
            )
            docker_failed = result.returncode != 0
        else:
            result = subprocess.run([docker, "system", "df"], check=False)
            print("WOULD_RUN docker system prune -af --volumes")
            docker_failed = result.returncode != 0
        if docker_failed:
            print("ERROR Docker cleanup command failed", file=sys.stderr)
    return 1 if docker_failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
