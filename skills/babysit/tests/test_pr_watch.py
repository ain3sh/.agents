from __future__ import annotations

import contextlib
import importlib.machinery
import importlib.util
import io
import json
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


def comment(author: str, kind: str, body: str) -> dict[str, Any]:
    return {
        "id": f"IC_{author}",
        "url": f"https://github.com/{REPO}/pull/{NUMBER}#issuecomment-1",
        "body": body,
        "createdAt": "2026-01-01T00:00:00Z",
        "updatedAt": "2026-01-01T00:00:00Z",
        "lastEditedAt": None,
        "author": {"login": author, "__typename": kind},
    }


def thread_comment(
    id: str, author: str, body: str, at: str, state: str = "SUBMITTED"
) -> dict[str, Any]:
    return {
        **comment(author, "User", body),
        "id": id,
        "url": f"https://github.com/{REPO}/pull/{NUMBER}#discussion_{id}",
        "createdAt": at,
        "state": state,
    }


def replied_pr(*, submitted: bool, resolved: bool) -> dict[str, Any]:
    """A human's top-level comment and review thread, both answered by one
    later marked reply that sits in the agent's own review: submitted, or
    still pending and so visible to the agent alone."""
    pr = pull_request("CLEAN")
    pr["comments"] = page(
        [{**comment("someone", "User", "Why?"), "createdAt": "2026-01-01T00:00:00Z"}]
    )
    pr["reviews"] = page(
        [
            {
                **comment("me", "User", ""),
                "id": "PRR_1",
                "url": f"https://github.com/{REPO}/pull/{NUMBER}#pullrequestreview-1",
                "state": "COMMENTED" if submitted else "PENDING",
                "submittedAt": "2026-01-03T00:00:00Z" if submitted else None,
                "comments": {"totalCount": 1},
            }
        ]
    )
    pr["reviewThreads"] = {
        "totalCount": 1,
        "nodes": [
            {
                "isResolved": resolved,
                "isOutdated": False,
                "path": "a.py",
                "line": 3,
                "comments": {
                    "nodes": [
                        thread_comment(
                            "r1", "someone", "Rename this.", "2026-01-02T00:00:00Z"
                        ),
                        thread_comment(
                            "r2",
                            "me",
                            f"Renamed.\n\n{pr_watch.AGENT_MARK}",
                            "2026-01-03T00:00:00Z",
                            "SUBMITTED" if submitted else "PENDING",
                        ),
                    ]
                },
            }
        ],
    }
    return pr


LINKBACK = (
    '<!-- linear-linkback -->\n<details>\n<summary><a href="https://linear.app/'
    'acme/issue/ENG-1/x">ENG-1 x</a></summary>\n</details>'
)


RULES = f"repos/{REPO}/rules/branches/dev"
ETAG = 'W/"1"'


def fake_gh(*args: str) -> str:
    """A ruleset requiring REQUIRED, unchanged since ETAG, and no readable
    classic protection. Any other read fails the test: the verdict rests on
    the PR query alone, never on how far the base moved since the fork point."""
    path = args[-1]
    if path == RULES:
        if f"If-None-Match: {ETAG}" in args:
            raise pr_watch.GhError("gh: HTTP 304")
        rules = [
            {"type": "deletion"},
            {
                "type": "required_status_checks",
                "parameters": {
                    "required_status_checks": [{"context": n} for n in REQUIRED]
                },
            },
        ]
        return f"HTTP/2.0 200 OK\r\nEtag: {ETAG}\r\n\r\n{json.dumps(rules)}"
    if path.endswith("/protection/required_status_checks"):
        raise pr_watch.GhError("gh: Resource not accessible by integration (HTTP 403)")
    raise AssertionError(f"unexpected gh call: {args}")


class OnceVerdictTest(unittest.TestCase):
    def setUp(self) -> None:
        state = tempfile.TemporaryDirectory()
        self.addCleanup(state.cleanup)
        self.gh = mock.Mock(side_effect=fake_gh)
        for patch in (
            mock.patch.object(pr_watch, "STATE_DIR", Path(state.name)),
            mock.patch.object(pr_watch, "gh", self.gh),
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

    def test_linear_linkback_is_not_feedback(self) -> None:
        pr = pull_request("CLEAN")
        pr["comments"] = page([comment("linear-code", "Bot", LINKBACK)])
        code, lines = self.once(pr)
        self.assertEqual(lines, [f"READY {REPO}#{NUMBER} @ {HEAD}"])
        self.assertEqual(code, 0)

    def test_other_comments_like_the_linkback_are_feedback(self) -> None:
        for author, kind, body in (
            ("linear-code", "Bot", "This issue was moved to Done."),
            ("someone", "User", LINKBACK),
        ):
            with self.subTest(author=author):
                pr = pull_request("CLEAN")
                pr["comments"] = page([comment(author, kind, body)])
                code, lines = self.once(pr)
                self.assertEqual(code, 1)
                self.assertTrue(lines[0].startswith(f"comment from {author}: "), lines)
                self.assertEqual(lines[-1], f"ACTION {REPO}#{NUMBER} @ {HEAD}")

    def test_pending_review_hides_replies_and_blocks_ready(self) -> None:
        url = f"https://github.com/{REPO}/pull/{NUMBER}"
        asked = f"comment from someone: Why? {url}#issuecomment-1"
        thread = f"thread from someone on a.py:3: Rename this. {url}#discussion_r1"
        pending = (
            "pending-review: your unsubmitted review hides comments (1) from "
            f"everyone else {url}#pullrequestreview-1"
        )
        verdict = f"ACTION {REPO}#{NUMBER} @ {HEAD}"
        for resolved, expected in (
            (False, [asked, thread, pending, verdict]),
            (True, [asked, pending, verdict]),
        ):
            with self.subTest(resolved=resolved):
                code, lines = self.once(replied_pr(submitted=False, resolved=resolved))
                self.assertEqual(lines, expected)
                self.assertEqual(code, 1)

    def test_submitted_reply_settles_its_thread_and_comment(self) -> None:
        code, lines = self.once(replied_pr(submitted=True, resolved=False))
        self.assertEqual(
            lines,
            [
                (
                    "unresolved review threads (1): "
                    f"https://github.com/{REPO}/pull/{NUMBER}#discussion_r1"
                ),
                f"ACTION {REPO}#{NUMBER} @ {HEAD}",
            ],
        )
        self.assertEqual(code, 1)
        code, lines = self.once(replied_pr(submitted=True, resolved=True))
        self.assertEqual(lines, [f"READY {REPO}#{NUMBER} @ {HEAD}"])
        self.assertEqual(code, 0)

    def test_later_runs_revalidate_required_checks_for_free(self) -> None:
        # Each --once is a new process: the second reads the first's cache,
        # revalidates the ruleset by ETag, and skips the denied protection read.
        for calls in (
            [mock.call("api", "--include", RULES), mock.ANY],
            [mock.call("api", "--include", "-H", f"If-None-Match: {ETAG}", RULES)],
        ):
            self.gh.reset_mock()
            code, lines = self.once(pull_request("CLEAN", checks=[check("lint")]))
            self.assertEqual(self.gh.call_args_list, calls)
            self.assertEqual(lines[0], "waiting: pending checks (1): test")
            self.assertEqual(code, 3)

    def test_an_unreadable_required_checks_cache_is_a_miss(self) -> None:
        path = (
            Path(pr_watch.STATE_DIR)
            / "required"
            / f"{REPO.replace('/', '%2F')}%3Adev.json"
        )
        path.parent.mkdir(parents=True)
        path.write_text("{not json")
        self.once(pull_request("CLEAN", checks=[check("lint")]))
        self.assertEqual(
            self.gh.call_args_list, [mock.call("api", "--include", RULES), mock.ANY]
        )
        self.assertEqual(json.loads(path.read_text())[RULES]["etag"], ETAG)

    def test_unapproved_clean_green_pr_waits_for_review(self) -> None:
        code, lines = self.once(pull_request("CLEAN", approved=False))
        self.assertEqual(
            lines,
            ["waiting: review: review required", f"WAIT {REPO}#{NUMBER} @ {HEAD}"],
        )
        self.assertEqual(code, 3)


class RequiredChecksErrorTest(unittest.TestCase):
    def test_only_a_final_404_or_403_is_cached_as_denied(self) -> None:
        for message, denied in (
            ("gh: Not Found (HTTP 404)", True),
            ("gh: Resource not accessible by integration (HTTP 403)", True),
            ("gh: Bad Gateway (HTTP 502) at /requests/403", False),
        ):
            with mock.patch.object(
                pr_watch, "gh", side_effect=pr_watch.GhError(message)
            ):
                if denied:
                    self.assertIn("denied", pr_watch.revalidate(RULES, {}, list))
                else:
                    self.assertRaises(
                        pr_watch.GhError, pr_watch.revalidate, RULES, {}, list
                    )

    def test_abuse_detection_is_a_rate_limit(self) -> None:
        self.assertTrue(
            pr_watch.RATE_LIMITED.search(
                "gh: You have triggered an abuse detection mechanism. (HTTP 403)"
            )
        )


if __name__ == "__main__":
    unittest.main()
