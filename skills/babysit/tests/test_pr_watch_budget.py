"""pr-watch's budget: pacing from response headers, and a loop that reads
`pulls/<n>` only when something changed."""

from __future__ import annotations

import contextlib
import importlib.machinery
import importlib.util
import io
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
    def test_pace_uses_observed_account_spend_not_a_fleet_estimate(self) -> None:
        budget = pr_watch.Budget()
        for _ in range(4):
            budget.record(answer(200, remaining=2192))
        self.assertEqual(budget.pace(300, RESET - 1800), 300)
        # Other machines also spent this bucket. Even our free 304 observes it.
        budget.record(answer(304, remaining=1792))
        self.assertEqual(budget.pace(300, RESET - 1500), 670)
        budget.record(answer(304, remaining=1792))
        self.assertEqual(budget.pace(300, RESET - 830), 300)

    def test_reset_and_resource_each_start_a_new_sample(self) -> None:
        budget = pr_watch.Budget()
        for _ in range(10):
            budget.record(answer(200, remaining=15000))
        budget.record(answer(200, remaining=10).replace("core", "graphql"))
        self.assertEqual(budget.pace(300, RESET - 1800), 360)
        budget.record(answer(304, remaining=0))
        self.assertEqual(budget.pace(300, RESET - 1440), 1445)
        budget.record(answer(200, remaining=14000).replace(str(RESET), "13600"))
        self.assertEqual(budget.pace(300, RESET + 1), 300)
        self.assertEqual(set(budget.buckets), {"core@13600"})


class RateLimitSleepTest(unittest.TestCase):
    def sleep_for(self, core: dict[str, int] | None, now: int = 1000) -> int:
        proc = subprocess.CompletedProcess(
            ["gh", "api", "rate_limit"], 1 if core is None else 0,
            "" if core is None else json.dumps({"resources": {"core": core}}), "",
        )
        with (
            mock.patch.object(pr_watch.subprocess, "run", return_value=proc) as run,
            mock.patch.object(pr_watch.time, "time", return_value=now),
            mock.patch.object(pr_watch.time, "sleep") as sleep,
            mock.patch.object(pr_watch.random, "randint", return_value=60),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            pr_watch.wait_for_rate_limit()
        run.assert_called_once_with(["gh", "api", "rate_limit"], check=False, capture_output=True, text=True)
        return sleep.call_args.args[0]

    def test_spent_primary_limit_sleeps_until_reset_with_a_one_hour_cap(self) -> None:
        for reset, expected in ((1300, 305), (9000, 3600), (900, 5)):
            with self.subTest(reset=reset):
                self.assertEqual(self.sleep_for({"remaining": 0, "reset": reset}), expected)

    def test_secondary_limit_or_failed_budget_read_sleeps_about_a_minute(self) -> None:
        for core in ({"remaining": 7974, "reset": 4490}, None):
            with self.subTest(core=core):
                self.assertEqual(self.sleep_for(core), 60)


class LoopTest(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        for patcher in (
            mock.patch.object(pr_watch, "STATE_DIR", Path(tmp.name)),
            mock.patch.object(pr_watch, "BUDGET", pr_watch.Budget()),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)
        self.head = "a" * 40
        self.base = "b" * 40
        self.merge = "blocked"
        self.calls: list[str] = []

    def body(self, url: str) -> Any:
        if url.endswith("/pulls/7"):
            return {"html_url": "u", "merged_at": None, "state": "open", "draft": False,
                    "head": {"sha": self.head, "ref": "feat", "repo": {"full_name": "o/r"}},
                    "base": {"ref": "dev", "sha": self.base}, "mergeable_state": self.merge, "labels": []}
        if "check-runs" in url:
            return {"check_runs": []}
        if url.endswith("/status?per_page=100"):
            return {"statuses": []}
        return []

    def gh(self, *args: str, unchanged: bool = False) -> str:
        if args[1] == "graphql":
            self.calls.append("reviews graphql")
            return answer(200, {"data": {"viewer": {"id": "me"}, "repository": {"pullRequest": {
                "reviews": {"nodes": [], "pageInfo": {"hasNextPage": False}},
            }}}})
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
        out = f"{self.head}\trefs/pull/7/head\n{self.head}\trefs/heads/feat\n{self.base}\trefs/heads/dev\n"
        return subprocess.CompletedProcess(args, 0, out, "")

    def poll(self, watcher: Any) -> list[str]:
        self.calls = []
        with mock.patch.object(pr_watch, "gh", self.gh), mock.patch.object(pr_watch.subprocess, "run", self.ls_remote):
            watcher.fetch()
        watcher.rest.save()
        return self.calls

    def test_steady_polls_read_the_head_by_git_and_never_the_pr(self) -> None:
        watcher = pr_watch.Watcher("o/r", 7, 300, once=False)
        first = self.poll(watcher)
        self.assertIn("repos/o/r/pulls/7", first)
        for _ in range(pr_watch.FULL_EVERY - 1):
            calls = self.poll(watcher)
            self.assertNotIn("repos/o/r/pulls/7", calls)
            self.assertNotIn("reviews graphql", calls)
            self.assertIn("ls-remote", calls)
        self.assertIn("repos/o/r/pulls/7", self.poll(watcher))

    def test_a_base_only_move_reads_conflict_on_the_next_poll(self) -> None:
        watcher = pr_watch.Watcher("o/r", 7, 300, once=False)
        self.poll(watcher)
        self.base, self.merge = "c" * 40, "dirty"
        self.assertIn("repos/o/r/pulls/7", self.poll(watcher))
        self.assertEqual(watcher.rest.cache["repos/o/r/pulls/7"]["body"]["mergeable_state"], "dirty")

    def test_a_moved_head_reads_the_pr(self) -> None:
        watcher = pr_watch.Watcher("o/r", 7, 300, once=False)
        self.poll(watcher)
        self.poll(watcher)
        self.head = "c" * 40
        self.assertIn("repos/o/r/pulls/7", self.poll(watcher))


if __name__ == "__main__":
    unittest.main()
