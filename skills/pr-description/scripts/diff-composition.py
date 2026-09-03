#!/usr/bin/env python3
"""Bucket a three-dot diff by review weight, from git numstat (ground truth).

    diff-composition.py BASE HEAD [--core PATH ...] [--tooling PREFIX ...] [--repo DIR]

Buckets, in order of precedence:
  generated  snapshot / lockfile / build-output paths
  tests      *.test.*, *.spec.*, __tests__, __fixtures__, fixtures/
  docs+ci    docs/, .github/, *.md, *.yml
  core       exactly the paths passed with --core (the files that carry behavior)
  tooling    paths under --tooling prefixes (harness, scripts; not shipped)
  mechanical everything else: the repeated pattern, moves, adoptions

Prints share / lines / files per bucket, then every core and mechanical file with
its line count so the largest ones can be described honestly in the body.
"""
import argparse
import re
import subprocess
from collections import defaultdict

GENERATED = re.compile(
    r"__ast-snapshots__|__snapshots__|\.snap$|package-lock\.json$|yarn\.lock$|pnpm-lock\.yaml$|/generated/|\.generated\.|dist/"
)
TESTS = re.compile(r"\.(test|spec)\.[cm]?[jt]sx?$|__tests__|__fixtures__|/fixtures/|\.fixture\.|_test\.py$|/test_[^/]+\.py$")
DOCS = re.compile(r"^docs/|^\.github/|\.md$|\.ya?ml$")


def bucket(path: str, core: set[str], tooling: tuple[str, ...]) -> str:
    if GENERATED.search(path):
        return "generated"
    if TESTS.search(path):
        return "tests"
    if DOCS.search(path):
        return "docs+ci"
    if path in core:
        return "core"
    if path.startswith(tooling):
        return "tooling"
    return "mechanical"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("base")
    ap.add_argument("head")
    ap.add_argument("--core", nargs="*", default=[], help="files that carry behavior")
    ap.add_argument("--tooling", nargs="*", default=[], help="path prefixes for harness/scripts")
    ap.add_argument("--repo", default=".")
    args = ap.parse_args()

    core = set(args.core)
    tooling = tuple(args.tooling)
    out = subprocess.check_output(
        ["git", "-C", args.repo, "diff", "--numstat", f"{args.base}...{args.head}"], text=True
    )
    lines: dict[str, int] = defaultdict(int)
    files: dict[str, list[tuple[int, str]]] = defaultdict(list)
    total = 0
    for row in out.splitlines():
        add, dele, path = row.split("\t")
        if add == "-":  # binary
            continue
        n = int(add) + int(dele)
        b = bucket(path, core, tooling)
        lines[b] += n
        files[b].append((n, path))
        total += n

    missing = core - {p for v in files.values() for _, p in v}
    if missing:
        print("WARNING --core paths not in diff:", *sorted(missing), sep="\n  ")

    print(f"total {total} lines, {sum(len(v) for v in files.values())} files")
    for b in ("generated", "mechanical", "tests", "core", "tooling", "docs+ci"):
        if lines[b]:
            print(f"{b:11} {100 * lines[b] / total:5.1f}%  {lines[b]:6} lines  {len(files[b]):3} files")
    for b in ("core", "mechanical"):
        if not files[b]:
            continue
        small = sum(1 for n, _ in files[b] if n <= 30)
        print(f"\n== {b} ({small} files change <=30 lines) ==")
        for n, p in sorted(files[b], reverse=True):
            print(f"  {n:5}  {p}")


if __name__ == "__main__":
    main()
