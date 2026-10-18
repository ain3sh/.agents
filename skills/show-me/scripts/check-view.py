#!/usr/bin/env python3
"""Exit 0 when Markdown holds a show-me view; exit 1 naming what is missing.

    check-view.py FILE [--section NAME]

A view is a line opening a fenced block (``` or ~~~), a table row (|), or an
image (![, <picture, <img). --section scopes the check to one `## NAME`
section. This is a cooperation guard: it proves a view exists, not that the
view is faithful or useful; show-me's checks own that.
"""
import argparse
import re
import sys

VIEW = re.compile(r"^(```|~~~|\||!\[|<picture|<img)")
FENCE = re.compile(r"^(```|~~~)")


def scope(lines, section):
    if section is None:
        return lines
    inside, in_fence, kept = False, False, []
    for line in lines:
        if FENCE.match(line):
            in_fence = not in_fence
        elif not in_fence and line.startswith("## "):
            inside = line[3:].strip() == section
            continue
        if inside:
            kept.append(line)
    return kept


def has_view(text, section=None):
    return any(VIEW.match(line) for line in scope(text.splitlines(), section))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file")
    parser.add_argument("--section")
    args = parser.parse_args()
    with open(args.file, encoding="utf-8") as handle:
        text = handle.read()
    if has_view(text, args.section):
        return 0
    where = f"`## {args.section}` of {args.file}" if args.section else args.file
    print(
        f"no show-me view in {where}: add a fenced block, table, or image",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
