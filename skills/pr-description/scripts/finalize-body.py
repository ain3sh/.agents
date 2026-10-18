#!/usr/bin/env python3
"""Make a PR body publishable: require its Architecture view, then stamp the marker.

    finalize-body.py BODY [--repo DIR]

Exits 1 without touching BODY when `## Architecture` holds no show-me view
(show-me/scripts/check-view.py owns what a view is). Otherwise drops every old
`pr-desc-base` marker and appends one for the repo's full HEAD sha as the final
line, after any generated block such as `stack:links`. Safe to rerun.
"""
import argparse
import importlib.util
import re
import subprocess
import sys
from pathlib import Path

CHECK_VIEW = Path(__file__).resolve().parents[2] / "show-me" / "scripts" / "check-view.py"
MARKER = re.compile(r"^<!-- pr-desc-base: [0-9a-f]+ -->\s*$")


def load_has_view():
    spec = importlib.util.spec_from_file_location("check_view", CHECK_VIEW)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.has_view


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("body")
    parser.add_argument("--repo", default=".")
    args = parser.parse_args()
    body = Path(args.body)
    text = body.read_text(encoding="utf-8")
    if not load_has_view()(text, "Architecture"):
        print(
            f"{body}: `## Architecture` holds no show-me view; draw one "
            "(pr-description references/workflow.md, Architecture) and rerun",
            file=sys.stderr,
        )
        return 1
    sha = subprocess.run(
        ["git", "-C", args.repo, "rev-parse", "HEAD"],
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    kept = [line for line in text.splitlines() if not MARKER.match(line)]
    while kept and not kept[-1].strip():
        kept.pop()
    body.write_text("\n".join(kept) + f"\n\n<!-- pr-desc-base: {sha} -->\n", encoding="utf-8")
    print(f"{body}: Architecture view present; stamped pr-desc-base {sha}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
