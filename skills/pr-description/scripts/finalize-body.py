#!/usr/bin/env python3
"""Make a PR body publishable: require its Architecture view, then stamp the markers.

    finalize-body.py BODY [--prior LIVE_BODY]

Exits 1 without touching BODY when FACTORY_SESSION_ID is unset or `## Architecture`
holds no show-me view (show-me/scripts/check-view.py owns what a view is).
Otherwise replaces the trailing markers with two lines, after any generated block
such as `stack:links`:

    <!-- pr-desc-sessions: <oldest> ... <newest> -->
    <!-- pr-desc-base: <full HEAD sha> -->

The sessions list keeps every id from LIVE_BODY, then from BODY, then appends this
session, each once in first-seen order. Safe to rerun.
"""
import argparse
import importlib.util
import os
import re
import subprocess
import sys
from pathlib import Path

CHECK_VIEW = Path(__file__).resolve().parents[2] / "show-me" / "scripts" / "check-view.py"
BASE_MARKER = re.compile(r"^<!-- pr-desc-base: [0-9a-f]+ -->\s*$")
SESSIONS_MARKER = re.compile(r"^<!-- pr-desc-sessions: (.+?) -->\s*$")


def load_has_view():
    spec = importlib.util.spec_from_file_location("check_view", CHECK_VIEW)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.has_view


def session_ids(text):
    return [
        sid
        for line in text.splitlines()
        if (match := SESSIONS_MARKER.match(line))
        for sid in match.group(1).split()
    ]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("body")
    parser.add_argument("--prior", help="live PR body whose sessions list must survive a marker-free draft")
    args = parser.parse_args()
    body = Path(args.body)
    text = body.read_text(encoding="utf-8")
    prior = Path(args.prior).read_text(encoding="utf-8") if args.prior else ""
    # Droid's Execute exports FACTORY_SESSION_ID to every command, on laptops and
    # remote computers alike; DROID_SESSION_ID comes from a local hook and is
    # absent on remote computers.
    session = os.environ.get("FACTORY_SESSION_ID")
    if not session:
        print(f"{body}: FACTORY_SESSION_ID is unset; run finalize from a Droid session", file=sys.stderr)
        return 1
    if not load_has_view()(text, "Architecture"):
        print(
            f"{body}: `## Architecture` holds no show-me view; draw one "
            "(pr-description references/workflow.md, Architecture) and rerun",
            file=sys.stderr,
        )
        return 1
    sha = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    sessions = " ".join(dict.fromkeys([*session_ids(prior), *session_ids(text), session]))
    kept = [
        line for line in text.splitlines()
        if not (BASE_MARKER.match(line) or SESSIONS_MARKER.match(line))
    ]
    while kept and not kept[-1].strip():
        kept.pop()
    body.write_text(
        "\n".join(kept)
        + f"\n\n<!-- pr-desc-sessions: {sessions} -->\n<!-- pr-desc-base: {sha} -->\n",
        encoding="utf-8",
    )
    print(f"{body}: Architecture view present; stamped pr-desc-sessions {sessions}, pr-desc-base {sha}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
