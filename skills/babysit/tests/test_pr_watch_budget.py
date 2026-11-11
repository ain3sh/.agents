"""pr-watch's budget: pacing from response headers, and a loop that reads
`pulls/<n>` only when something changed."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

PATH = Path(__file__).resolve().parents[1] / "scripts" / "pr-watch"
loader = importlib.machinery.SourceFileLoader("pr_watch_budget", str(PATH))
spec = importlib.util.spec_from_loader(loader.name, loader)
assert spec
pr_watch = importlib.util.module_from_spec(spec)
loader.exec_module(pr_watch)

RESET = 10_000


def answer(status: int, body: Any = None, etag: str = "e1", remaining: int = 9000) -> str:
    head = (
        f"HTTP/2.0 {status} {'OK' if status == 200 else 'Not Modified'}\n"
        f"Etag: {etag}\nX-Ratelimit-Limit: 15000\nX-Ratelimit-Remaining: {remaining}\n"
        f"X-Ratelimit-Reset: {RESET}\nX-Ratelimit-Resource: core\n"
    )
    return head + "\n" + ("" if body is None else json.dumps(body))


class BudgetTest(unittest.TestCase):
    def test_every_status_but_304_counts_and_each_reset_is_its_own_bucket(self) -> None:
        budget = pr_watch.Budget()
        self.assertEqual(budget.record(answer(200, {"a": 1}))[0], 200)
        self.assertEqual(budget.record(answer(304, remaining=8000))[0], 304)
        budget.record(answer(200, {}, remaining=6000).replace(str(RESET), "9000"))
        self.assertEqual(budget.take(), 2)
        self.assertEqual(budget.take(), 0)
        self.assertEqual(sorted(b["remaining"] for b in budget.buckets.values()), [6000, 8000])

    def pace(self, remaining: int, calls: float, now: float = RESET - 3600) -> int:
        budget = pr_watch.Budget()
        budget.record(answer(304, remaining=remaining))
        return budget.pace(300, calls, now)

    def test_a_poll_of_every_watcher_never_spends_more_than_half_of_what_is_left(self) -> None:
        for remaining in (15000, 8000, 3000, 900):
            for calls in (0.2, 1, 2.5, 8):
                delay = self.pace(remaining, calls)
                polls = 3600 / delay
                if calls * pr_watch.WATCHERS <= remaining / 2:
                    self.assertLessEqual(polls * calls * pr_watch.WATCHERS, remaining / 2 + 1e-6)
                else:
                    self.assertEqual(delay, 3605)

    def test_free_polls_run_at_the_interval(self) -> None:
        self.assertEqual(self.pace(100, 0), 300)

    def test_a_past_reset_is_forgotten(self) -> None:
        self.assertEqual(self.pace(10, 5, now=RESET + 1), 300)


class LoopTest(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        patcher = mock.patch.object(pr_watch, "STATE_DIR", Path(tmp.name))
        patcher.start()
        self.addCleanup(patcher.stop)
        self.head = "a" * 40
        self.calls: list[str] = []
        self.etags: dict[str, str] = {}

    def body(self, url: str) -> Any:
        if url.endswith("/pulls/7"):
            return {"html_url": "u", "merged_at": None, "state": "open", "draft": False,
                    "head": {"sha": self.head, "ref": "feat", "repo": {"full_name": "o/r"}},
                    "base": {"ref": "dev", "sha": "b" * 40}, "mergeable_state": "blocked", "labels": []}
        if "check-runs" in url:
            return {"check_runs": []}
        if url.endswith("/status?per_page=100"):
            return {"statuses": []}
        return []

    def gh(self, *args: str, ride: bool = True, unchanged: bool = False) -> str:
        url = args[-1]
        self.calls.append(url)
        if "rules/branches" in url or "protection" in url:
            return answer(200, [] if "rules" in url else {"contexts": []})
        pr = url.endswith("/pulls/7")
        etag = f"{url}:{self.head if pr else ''}"
        # The PR never answers 304: it embeds the repository's pushed_at.
        if any(a == f"If-None-Match: {etag}" for a in args) and not pr:
            return answer(304, etag=etag)
        return answer(200, self.body(url), etag=etag)

    def ls_remote(self, *args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        self.calls.append("ls-remote")
        out = f"{self.head}\trefs/pull/7/head\n{self.head}\trefs/heads/feat\n"
        return subprocess.CompletedProcess(args, 0, out, "")

    def poll(self, watcher: Any) -> list[str]:
        self.calls = []
        with mock.patch.object(pr_watch, "gh", self.gh), mock.patch.object(pr_watch.subprocess, "run", self.ls_remote):
            watcher.fetch()
        watcher.rest.save({})
        return self.calls

    def test_steady_polls_read_the_head_by_git_and_never_the_pr(self) -> None:
        watcher = pr_watch.Watcher("o/r", 7, 300, once=False)
        first = self.poll(watcher)
        self.assertIn("repos/o/r/pulls/7", first)
        pr_watch.BUDGET.take()
        for _ in range(pr_watch.FULL_EVERY - 1):
            calls = self.poll(watcher)
            self.assertNotIn("repos/o/r/pulls/7", calls)
            self.assertIn("ls-remote", calls)
        self.assertEqual(pr_watch.BUDGET.take(), 0)
        self.assertIn("repos/o/r/pulls/7", self.poll(watcher))

    def test_a_moved_head_reads_the_pr(self) -> None:
        watcher = pr_watch.Watcher("o/r", 7, 300, once=False)
        self.poll(watcher)
        self.poll(watcher)
        self.head = "c" * 40
        self.assertIn("repos/o/r/pulls/7", self.poll(watcher))


if __name__ == "__main__":
    unittest.main()
