from __future__ import annotations

import contextlib
import importlib.machinery
import importlib.util
import io
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

SCRIPT = Path(__file__).parents[1] / "scripts" / "pr-watch"
_loader = importlib.machinery.SourceFileLoader("pr_watch", str(SCRIPT))
pr_watch = importlib.util.module_from_spec(
    importlib.util.spec_from_loader("pr_watch", _loader)
)
_loader.exec_module(pr_watch)

REPO = "o/r"
NUMBER = 7
HEAD = "a" * 40
BASE_OID = "b" * 40
REQUIRED = ("lint", "test")


def check(name: str, conclusion: str = "SUCCESS") -> dict[str, Any]:
    return {
        "__typename": "CheckRun",
        "id": f"run-{name}",
        "name": name,
        "status": "COMPLETED",
        "conclusion": conclusion,
        "detailsUrl": f"https://ci/{name}",
    }


def page(nodes: list[Any]) -> dict[str, Any]:
    return {"pageInfo": {"hasPreviousPage": False}, "nodes": nodes}


def pull_request(
    state: str, *, approved: bool = True, checks: list[Any] | None = None
) -> dict[str, Any]:
    return {
        "id": "PR_1",
        "url": f"https://github.com/{REPO}/pull/{NUMBER}",
        "state": "OPEN",
        "isDraft": False,
        "headRefOid": HEAD,
        "baseRefName": "dev",
        "mergeStateStatus": state,
        "reviewDecision": "APPROVED" if approved else "REVIEW_REQUIRED",
        "baseRef": {"target": {"oid": BASE_OID}},
        "commits": {
            "nodes": [
                {
                    "commit": {
                        "id": "C_1",
                        "statusCheckRollup": {
                            "contexts": {
                                "pageInfo": {"hasNextPage": False},
                                "nodes": checks
                                if checks is not None
                                else [check(n) for n in REQUIRED],
                            }
                        },
                    }
                }
            ]
        },
        "latestOpinionatedReviews": {
            "nodes": [{"state": "APPROVED"}] if approved else []
        },
        "labels": {"nodes": []},
        "comments": page([]),
        "reviews": page([]),
        "reviewThreads": {"totalCount": 0, "nodes": []},
    }


def fake_gh(*args: str) -> str:
    """A ruleset requiring REQUIRED and no readable classic protection. Any
    other read fails the test: the verdict rests on the PR query alone, never
    on how far the base moved since the fork point."""
    path = args[1]
    if path == f"repos/{REPO}/rules/branches/dev":
        return "\n".join(REQUIRED) + "\n"
    if path.endswith("/protection/required_status_checks"):
        raise pr_watch.GhError("HTTP 403: Resource not accessible by integration")
    raise AssertionError(f"unexpected gh call: {args}")


class OnceVerdictTest(unittest.TestCase):
    def setUp(self) -> None:
        state = tempfile.TemporaryDirectory()
        self.addCleanup(state.cleanup)
        for patch in (
            mock.patch.object(pr_watch, "STATE_DIR", Path(state.name)),
            mock.patch.object(pr_watch, "gh", fake_gh),
        ):
            patch.start()
            self.addCleanup(patch.stop)

    def once(self, pr: dict[str, Any]) -> tuple[int, list[str]]:
        """Run `pr-watch --once` against pr; return its exit code and stdout lines."""
        out = io.StringIO()
        data = {"repository": {"pullRequest": pr}}
        with (
            mock.patch.object(pr_watch, "graphql", return_value=data),
            contextlib.redirect_stdout(out),
            contextlib.redirect_stderr(io.StringIO()),
            self.assertRaises(SystemExit) as exit,
        ):
            pr_watch.Watcher(REPO, NUMBER, 30, once=True).poll()
        return exit.exception.code, out.getvalue().splitlines()

    def test_approved_mergeable_green_pr_is_ready(self) -> None:
        for state, checks in (
            ("CLEAN", None),
            ("HAS_HOOKS", None),
            ("UNSTABLE", [*map(check, REQUIRED), check("optional", "FAILURE")]),
        ):
            with self.subTest(state=state):
                code, lines = self.once(pull_request(state, checks=checks))
                self.assertEqual(lines, [f"READY {REPO}#{NUMBER} @ {HEAD}"])
                self.assertEqual(code, 0)

    def test_conflict_needs_action(self) -> None:
        code, lines = self.once(pull_request("DIRTY"))
        self.assertEqual(code, 1)
        self.assertEqual(lines[0], "conflict: the branch conflicts with dev")
        self.assertEqual(lines[-1], f"ACTION {REPO}#{NUMBER} @ {HEAD}")

    def test_behind_a_strict_base_needs_action(self) -> None:
        # GitHub reports BEHIND only when the base requires an up-to-date
        # branch; a behind PR on a non-strict base reads CLEAN, so BEHIND is
        # the whole strictness signal.
        code, lines = self.once(pull_request("BEHIND"))
        self.assertEqual(code, 1)
        self.assertTrue(lines[0].startswith("behind: "), lines)
        self.assertEqual(lines[-1], f"ACTION {REPO}#{NUMBER} @ {HEAD}")

    def test_unapproved_clean_green_pr_waits_for_review(self) -> None:
        code, lines = self.once(pull_request("CLEAN", approved=False))
        self.assertEqual(
            lines,
            ["waiting: review: review required", f"WAIT {REPO}#{NUMBER} @ {HEAD}"],
        )
        self.assertEqual(code, 3)


if __name__ == "__main__":
    unittest.main()
