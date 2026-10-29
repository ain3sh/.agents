#!/usr/bin/env python3
"""Exit 0 when Markdown holds a show-me view; exit 1 naming what is missing.

    check-view.py FILE [--section NAME]

A view is a line opening a fenced block (``` or ~~~), a table row (|), or an
image (![, <picture, <img), at any indentation, so views nested under list
items count. --section scopes the check to one `## NAME` section. This is a
cooperation guard: it proves a view exists, not that the view is faithful or
useful; show-me's checks own that.
"""
import argparse
import re
import sys

VIEW = re.compile(r"^\s*(```|~~~|\||!\[|<picture|<img)")
FENCE = re.compile(r"^\s*(`{3,}|~{3,})(.*)$")
HEADING = re.compile(r"^ {0,3}## (.*?)(?:\s+#+)?\s*$")


def scope(lines, section):
    if section is None:
        return lines
    inside, fence, kept = False, None, []
    for line in lines:
        match = FENCE.match(line)
        if fence is None and match:
            fence = match.group(1)
        elif (fence and match and match.group(1)[0] == fence[0]
                and len(match.group(1)) >= len(fence) and not match.group(2).strip()):
            fence = None
        elif fence is None and (heading := HEADING.match(line)):
            inside = heading.group(1) == section
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
