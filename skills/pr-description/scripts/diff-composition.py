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

Prints additions, deletions, and whole-file adds/deletes per bucket, core first,
then every core and mechanical file with its own +/- and whether the diff adds or
deletes it whole.
Added lines are what a reviewer reads; deleted lines are checked for over-reach.
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
ORDER = ("core", "tests", "mechanical", "generated", "tooling", "docs+ci")


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


def git(repo: str, *args: str) -> str:
    return subprocess.check_output(["git", "-C", repo, *args], text=True)


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
    rng = f"{args.base}...{args.head}"
    whole = {p: "new file" for p in git(args.repo, "diff", "--name-only", "--diff-filter=A", rng).split()}
    whole |= {p: "deleted" for p in git(args.repo, "diff", "--name-only", "--diff-filter=D", rng).split()}

    totals: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    files: dict[str, list[tuple[int, int, str]]] = defaultdict(list)
    for row in git(args.repo, "diff", "--numstat", rng).splitlines():
        add, dele, path = row.split("\t")
        if add == "-":  # binary
            continue
        a, d = int(add), int(dele)
        b = bucket(path, core, tooling)
        totals[b][0] += a
        totals[b][1] += d
        files[b].append((a, d, path))

    missing = core - {p for v in files.values() for _, _, p in v}
    if missing:
        print("WARNING --core paths not in diff:", *sorted(missing), sep="\n  ")

    add_all = sum(t[0] for t in totals.values())
    del_all = sum(t[1] for t in totals.values())
    print(f"total +{add_all} / -{del_all}, {sum(len(v) for v in files.values())} files\n")
    print(f"{'bucket':11} {'+':>7} {'-':>7} {'files':>6} {'new':>4} {'deleted':>8}")
    for b in ORDER:
        if files[b]:
            kinds = [whole.get(p) for _, _, p in files[b]]
            print(
                f"{b:11} {totals[b][0]:7} {totals[b][1]:7} {len(files[b]):6}"
                f" {kinds.count('new file'):4} {kinds.count('deleted'):8}"
            )
    for b in ("core", "mechanical"):
        if not files[b]:
            continue
        small = sum(1 for a, d, _ in files[b] if a + d <= 30)
        print(f"\n== {b} ({small} files change <=30 lines) ==")
        for a, d, p in sorted(files[b], key=lambda f: (-f[0], -f[1], f[2])):
            note = f"  ({whole[p]})" if p in whole else ""
            print(f"  +{a:<5} -{d:<5} {p}{note}")


if __name__ == "__main__":
    main()
