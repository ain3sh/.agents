from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from hooks.pre_tool_use.wait_guard import _violation

WAIT_GUARD = Path(__file__).resolve().parents[1] / "pre_tool_use" / "wait_guard.py"

INCIDENT = (
    "sleep 90; for i in $(seq 1 50); do gh pr checks 30614 --repo "
    "Factory-AI/factory-mono > /tmp/c4.txt 2>&1; "
    "p=$(awk -F'\\t' '$2==\"pending\"' /tmp/c4.txt | wc -l); "
    '[ "$p" = 0 ] && break; sleep 60; done; '
    "awk -F'\\t' '{print $2}' /tmp/c4.txt | sort | uniq -c"
)


class WaitGuardTest(unittest.TestCase):
    def analyze(self, command: str, *, background: bool = False) -> str | None:
        return _violation(command, fire_and_forget=background)

    def test_rejects_the_incident_poll_loop(self) -> None:
        self.assertEqual(
            self.analyze(INCIDENT), "this polls GitHub state with sleep or watch"
        )
        self.assertIsNotNone(self.analyze(INCIDENT, background=True))

    def test_rejects_while_loops_and_api_polls(self) -> None:
        command = (
            "while true; do gh api repos/o/r/commits/abc/check-runs "
            "--jq .total_count; sleep 30; done"
        )
        self.assertIsNotNone(self.analyze(command))
        self.assertIsNotNone(self.analyze("watch -n 60 gh run list --limit 3"))

    def test_rejects_foreground_blocking_watch_only(self) -> None:
        for command in ("gh run watch 123 --exit-status", "gh pr checks 7 --watch"):
            self.assertEqual(
                self.analyze(command), "this blocks the turn on a GitHub watch"
            )
            self.assertIsNone(self.analyze(command, background=True))

    def test_allows_one_shot_queries_and_the_watcher(self) -> None:
        for command in (
            "gh pr checks 30614 --repo Factory-AI/factory-mono",
            "gh run view 41528162681 --log-failed",
            "~/.agents/skills/babysit/scripts/pr-watch 30614 --repo o/r",
            "sleep 5 && curl -s localhost:3000/health",
            "gh run rerun 41528162681 --failed",
        ):
            self.assertIsNone(self.analyze(command), command)

    def test_ignores_heredoc_bodies(self) -> None:
        command = "cat > /tmp/notes.md <<'EOF'\nsleep 60; gh pr checks 1\nEOF"
        self.assertIsNone(self.analyze(command))

    def test_registered_hook_denies_with_the_watcher_grammar(self) -> None:
        payload = {
            "session_id": "s",
            "transcript_path": "/tmp/t.jsonl",
            "cwd": "/tmp",
            "permission_mode": "default",
            "hook_event_name": "PreToolUse",
            "tool_name": "Execute",
            "tool_input": {"command": INCIDENT},
        }
        result = subprocess.run(
            [sys.executable, str(WAIT_GUARD)],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertIn("pr-watch", result.stdout + result.stderr)
        self.assertIn("deny", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
