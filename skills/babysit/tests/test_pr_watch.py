from __future__ import annotations

import contextlib
import hashlib
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
from urllib.parse import unquote

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
RULES = f"repos/{REPO}/rules/branches/dev"
PROTECTION = f"repos/{REPO}/branches/dev/protection/required_status_checks"
FREE = "free"
NOW = 1_800_000_000


def response(body: Any, *, status: int = 200, resource: str = "core", link: str = "") -> str:
    encoded = json.dumps(body)
    etag = f'"{hashlib.sha1(encoded.encode()).hexdigest()}"'
    return (
        f"HTTP/2.0 {status}\r\nEtag: {etag}\r\n"
        f"X-Ratelimit-Resource: {resource}\r\nX-Ratelimit-Remaining: 9000\r\n"
        f"X-Ratelimit-Limit: 15000\r\nX-Ratelimit-Reset: {NOW + 3600}\r\n"
        + (f'Link: <{link}>; rel="next"\r\n' if link else "")
        + "\r\n"
        + (encoded if status != 304 else "")
    )


def check(name: str, conclusion: str = "success") -> dict[str, Any]:
    return {
        "id": int(hashlib.sha1(f"{name}:{conclusion}".encode()).hexdigest()[:8], 16),
        "name": name,
        "status": "completed",
        "conclusion": conclusion,
        "html_url": f"https://ci/{name}",
        "details_url": f"https://ci/{name}",
    }


def comment(
    author: str, kind: str, body: str, *, id: int = 1, at: str = "2026-01-01T00:00:00Z"
) -> dict[str, Any]:
    return {
        "id": id,
        "node_id": f"N_{id}",
        "html_url": f"https://github.com/{REPO}/pull/{NUMBER}#issuecomment-{id}",
        "body": body,
        "created_at": at,
        "updated_at": at,
        "user": {"login": author + ("[bot]" if kind == "Bot" else ""), "type": kind},
    }


def pr_node(
    head: str, base: str, head_repo: str | None = REPO, base_repo: str = REPO
) -> dict[str, Any]:
    return {
        "head": {"ref": head, "repo": head_repo and {"full_name": head_repo}},
        "base": {"ref": base, "repo": {"full_name": base_repo}},
    }


def forks(branch: str) -> list[dict[str, Any]]:
    return [
        pr_node(branch, branch, base_repo="fork/r"),
        pr_node(branch, branch, head_repo=None, base_repo="fork/r"),
        pr_node(branch, "dev", head_repo="fork/r"),
    ]


class GitHub:
    """Only the REST resources pr-watch reads, plus GraphQL thread resolution."""

    def __init__(
        self, state: str, *, approved: bool = True, checks: list[Any] | None = None
    ) -> None:
        self.pr = {
            "html_url": f"https://github.com/{REPO}/pull/{NUMBER}",
            "state": "open",
            "merged_at": None,
            "draft": False,
            "head": {"sha": HEAD, "ref": "feat", "repo": {"full_name": REPO}},
            "base": {"ref": "dev", "sha": BASE_OID},
            "mergeable_state": state.lower(),
            "labels": [],
        }
        self.checks = checks if checks is not None else [check(n) for n in REQUIRED]
        self.statuses: list[Any] = []
        self.comments: list[Any] = []
        self.reviews = [
            {
                **comment("approver", "User", "", id=100),
                "state": "APPROVED",
                "submitted_at": "2026-01-01T00:00:00Z",
            }
        ] if approved else []
        self.notes: list[Any] = []
        self.resolved: dict[int, bool] = {}
        self.heads: dict[str, list[Any]] = {}
        self.annotations: dict[int, list[str]] = {}

    def body(self, url: str) -> Any:
        repo = f"repos/{REPO}"
        if url == f"{repo}/pulls/{NUMBER}":
            return self.pr
        if url == f"{repo}/commits/{self.pr['head']['sha']}/check-runs?per_page=100":
            return {"check_runs": self.checks}
        if url == f"{repo}/commits/{self.pr['head']['sha']}/status?per_page=100":
            return {"statuses": self.statuses}
        if url == f"{repo}/issues/{NUMBER}/comments?per_page=100":
            return self.comments
        if url == f"{repo}/pulls/{NUMBER}/reviews?per_page=100":
            return self.reviews
        if url == f"{repo}/pulls/{NUMBER}/comments?per_page=100":
            return self.notes
        if url.startswith(f"{repo}/pulls?state=open&per_page=100&head=o:"):
            return self.heads.get(unquote(url.split("head=o:", 1)[1]), [])
        if url.startswith(f"{repo}/check-runs/") and url.endswith("/annotations?per_page=100"):
            run = int(url.split("/check-runs/", 1)[1].split("/")[0])
            return [{"title": title} for title in self.annotations.get(run, [])]
        if url == RULES:
            return [
                {"type": "deletion"},
                {
                    "type": "required_status_checks",
                    "parameters": {"required_status_checks": [{"context": n} for n in REQUIRED]},
                },
            ]
        if url == f"{repo}/rules/branches/{FREE}":
            return []
        if url in (PROTECTION, f"{repo}/branches/{FREE}/protection/required_status_checks"):
            raise pr_watch.GhError("gh: Resource not accessible by integration (HTTP 403)")
        raise AssertionError(f"unexpected REST read: {url}")

    def gh(self, *args: str, ride: bool = True, unchanged: bool = False) -> str:
        assert args[0] == "api" and "--include" in args, args
        if args[1] == "graphql":
            assert f"query={pr_watch.THREADS}" in args and not ride, args
            assert "owner=o" in args and "name=r" in args and "number=7" in args, args
            return response(
                {"data": {"repository": {"pullRequest": {"reviewThreads": {"nodes": [
                    {"isResolved": resolved, "comments": {"nodes": [{"databaseId": root}]}}
                    for root, resolved in self.resolved.items()
                ]}}}}},
                resource="graphql",
            )
        url, _, page = args[-1].removeprefix("https://api.github.com/").partition("&page=")
        body = self.body(url)
        link = ""
        if isinstance(body, list):
            start = (int(page or "1") - 1) * 100
            if len(body) > start + 100:
                link = f"https://api.github.com/{url}&page={int(page or '1') + 1}"
            body = body[start:start + 100]
        out = response(body, link=link)
        etag = pr_watch.header(out.split("\r\n\r\n")[0], "etag")
        # Pull objects and lists embed pushed_at and do not answer 304.
        if f"{REPO}/pulls" not in url or "/reviews?" in url or "/comments?" in url:
            if f"If-None-Match: {etag}" in args:
                assert unchanged, args
                return response(body, status=304, link=link)
        return out

    def ls_remote(self, args: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        assert args == [
            "git", "-c", "credential.helper=", "-c", "credential.helper=!gh auth git-credential",
            "ls-remote", f"https://github.com/{REPO}.git", "refs/pull/7/head", "refs/heads/feat",
        ], args
        head = self.pr["head"]["sha"]
        return subprocess.CompletedProcess(args, 0, f"{head}\trefs/pull/7/head\n{head}\trefs/heads/feat\n", "")

    def stack(self, branches: tuple[str, ...], *, noise: bool = False) -> None:
        self.pr["base"]["ref"] = branches[0]
        for i, branch in enumerate(branches):
            if branch not in self.heads:
                self.heads[branch] = [
                    *(forks(branch) if noise else []),
                    *([pr_node(branch, branches[i + 1])] if i + 1 < len(branches) else []),
                ]


def replied_pr(*, submitted: bool, resolved: bool) -> GitHub:
    """One marked review reply settles feedback only after submission."""
    github = GitHub("CLEAN")
    github.comments = [comment("someone", "User", "Why?")]
    github.reviews.append({
        **comment("me", "User", "", id=101),
        "html_url": f"https://github.com/{REPO}/pull/{NUMBER}#pullrequestreview-101",
        "state": "COMMENTED" if submitted else "PENDING",
        "submitted_at": "2026-01-03T00:00:00Z" if submitted else None,
    })
    github.notes = [
        {
            **comment("someone", "User", "Rename this.", at="2026-01-02T00:00:00Z"),
            "html_url": f"https://github.com/{REPO}/pull/{NUMBER}#discussion_1",
            "path": "a.py", "line": 3, "original_line": 3,
        },
        {
            **comment("me", "User", f"Renamed.\n\n{pr_watch.AGENT_MARK}", id=2, at="2026-01-03T00:00:00Z"),
            "html_url": f"https://github.com/{REPO}/pull/{NUMBER}#discussion_2",
            "in_reply_to_id": 1, "pull_request_review_id": 101,
            "path": "a.py", "line": 3, "original_line": 3,
        },
    ]
    github.resolved = {1: resolved}
    return github


LINKBACK = (
    '<!-- linear-linkback -->\n<details>\n<summary><a href="https://linear.app/'
    'acme/issue/ENG-1/x">ENG-1 x</a></summary>\n</details>'
)

# factory-mono#28805: dev's base-filtered test never reports on the stack,
# while an optional Vercel status fails and duplicate Validate PR runs cancel.
STACK_28805 = (
    "ainesh/ac-2025-droid-rest",
    "ainesh/ac-2025-droid-cli",
    "ainesh/ac-2025-script-paths",
    "dev",
)
VERCEL = "Vercel – delegation-router-dev"
VERCEL_FAILED = f"check-failed {VERCEL} (optional) https://vercel.com/factory/delegation-router-dev"


def pr_28805() -> GitHub:
    github = GitHub("UNSTABLE", checks=[check("lint"), check("Validate PR", "cancelled"), check("Validate PR")])
    github.statuses = [{
        "context": VERCEL, "state": "failure",
        "target_url": "https://vercel.com/factory/delegation-router-dev",
    }]
    return github


class OnceVerdictTest(unittest.TestCase):
    def setUp(self) -> None:
        state = tempfile.TemporaryDirectory()
        self.addCleanup(state.cleanup)
        self.gh = mock.Mock()
        self.remote = mock.Mock()
        for patch in (
            mock.patch.object(pr_watch, "STATE_DIR", Path(state.name)),
            mock.patch.object(pr_watch, "BUDGET", pr_watch.Budget()),
            mock.patch.object(pr_watch, "gh", self.gh),
            mock.patch.object(pr_watch.subprocess, "run", self.remote),
            mock.patch.object(pr_watch.time, "time", return_value=NOW),
            mock.patch.object(pr_watch.time, "sleep", side_effect=AssertionError("unexpected sleep")),
        ):
            patch.start()
            self.addCleanup(patch.stop)

    def poll(self, github: GitHub, watcher: Any = None) -> tuple[int | None, list[str]]:
        watcher = watcher or pr_watch.Watcher(REPO, NUMBER, 300, once=True)
        self.gh.side_effect = github.gh
        self.remote.side_effect = github.ls_remote
        out = io.StringIO()
        code = None
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            try:
                if watcher.once:
                    watcher.run()
                else:
                    watcher.poll()
                    watcher.rest.save({"threads": watcher.threads})
            except SystemExit as exit:
                code = exit.code
        return code, out.getvalue().splitlines()

    def test_approved_mergeable_green_pr_is_ready(self) -> None:
        failed = "check-failed optional (optional) https://ci/optional"
        for state, checks, listed in (
            ("CLEAN", None, []),
            ("HAS_HOOKS", None, []),
            ("UNSTABLE", [*map(check, REQUIRED), check("optional", "failure")], [failed]),
        ):
            with self.subTest(state=state):
                self.assertEqual(
                    self.poll(GitHub(state, checks=checks)),
                    (0, [*listed, f"READY {REPO}#{NUMBER} @ {HEAD}"]),
                )

    def test_failed_optional_check_is_listed_beside_a_wait(self) -> None:
        github = GitHub("BLOCKED", approved=False, checks=[*map(check, REQUIRED), check("prem", "failure")])
        self.assertEqual(self.poll(github), (3, [
            "check-failed prem (optional) https://ci/prem",
            "waiting: review: no approval", f"WAIT {REPO}#{NUMBER} @ {HEAD}",
        ]))

    def test_conflict_needs_action(self) -> None:
        self.assertEqual(self.poll(GitHub("DIRTY")), (1, [
            "conflict: the branch conflicts with dev", f"ACTION {REPO}#{NUMBER} @ {HEAD}",
        ]))

    def test_behind_a_strict_base_needs_action(self) -> None:
        self.assertEqual(self.poll(GitHub("BEHIND")), (1, [
            "behind: branch protection requires the branch to be current with dev",
            f"ACTION {REPO}#{NUMBER} @ {HEAD}",
        ]))

    def test_linear_linkback_is_not_feedback(self) -> None:
        github = GitHub("CLEAN")
        github.comments = [comment("linear-code", "Bot", LINKBACK)]
        self.assertEqual(self.poll(github), (0, [f"READY {REPO}#{NUMBER} @ {HEAD}"]))

    def test_other_comments_like_the_linkback_are_feedback(self) -> None:
        for author, kind, body in (
            ("linear-code", "Bot", "This issue was moved to Done."),
            ("someone", "User", LINKBACK),
        ):
            with self.subTest(author=author):
                github = GitHub("CLEAN")
                github.comments = [comment(author, kind, body)]
                code, lines = self.poll(github)
                self.assertEqual(code, 1)
                self.assertTrue(lines[0].startswith(f"comment from {author}: "), lines)
                self.assertEqual(lines[-1], f"ACTION {REPO}#{NUMBER} @ {HEAD}")

    def test_a_bots_edit_after_the_agents_response_reopens_its_comment(self) -> None:
        # factory-mono#28661: a QA report was edited to FAILED after our reply.
        qa = comment("factory-droid", "Bot", "<!-- qa-report -->\n## QA: FAILED (32 / 34)")
        reply = comment("me", "User", f"Fixed.\n\n{pr_watch.AGENT_MARK}", id=2, at="2026-01-02T00:00:00Z")
        status = {**comment("github-actions", "Bot", "Deployed", id=3), "updated_at": "2026-01-03T00:00:00Z"}
        for edited, expected in (
            ("2026-01-03T00:00:00Z", (1, [
                f"comment from factory-droid: ## QA: FAILED (32 / 34) {qa['html_url']}",
                f"ACTION {REPO}#{NUMBER} @ {HEAD}",
            ])),
            (qa["created_at"], (0, [f"READY {REPO}#{NUMBER} @ {HEAD}"])),
            ("2026-01-01T12:00:00Z", (0, [f"READY {REPO}#{NUMBER} @ {HEAD}"])),
        ):
            with self.subTest(edited=edited):
                github = GitHub("CLEAN")
                github.comments = [{**qa, "updated_at": edited}, reply, status]
                self.assertEqual(self.poll(github), expected)

    def test_the_e2e_gate_waits_whether_its_status_runs_fail_or_skip(self) -> None:
        # New heads annotate plan and skip unrendered job names; old heads
        # fail each status run with the same approval-gate annotation.
        gate = [pr_watch.GATE_TITLE]
        skipped = check("test${{ needs.plan.outputs.wait }}", "skipped")
        waiting = "waiting: E2E gate (1 checks): runs once approved or labelled e2e:run"
        review = "waiting: review: no approval"
        pending = "waiting: pending checks (1): test"
        for name, approved, checks, notes, expected in (
            ("plan notice", False, [check("lint"), check("plan"), skipped],
             {check("plan")["id"]: gate}, [waiting, review]),
            ("failed status run", False, [check("lint"), check("test", "failure")],
             {check("test", "failure")["id"]: gate}, [waiting, review]),
            ("no notice", False, [check("lint"), check("plan"), skipped], {}, [pending, review]),
            ("approved", True, [check("lint"), check("plan"), skipped],
             {check("plan")["id"]: gate}, [pending]),
        ):
            with self.subTest(name=name):
                github = GitHub("CLEAN", approved=approved, checks=checks)
                github.annotations = notes
                self.assertEqual(self.poll(github), (3, [*expected, f"WAIT {REPO}#{NUMBER} @ {HEAD}"]))

    def test_pending_review_hides_replies_and_blocks_ready(self) -> None:
        url = f"https://github.com/{REPO}/pull/{NUMBER}"
        asked = f"comment from someone: Why? {url}#issuecomment-1"
        thread = f"thread from someone on a.py:3: Rename this. {url}#discussion_1"
        pending = (
            "pending-review: your unsubmitted review hides comments (1) from "
            f"everyone else {url}#pullrequestreview-101"
        )
        for resolved, expected in (
            (False, [asked, thread, pending]),
            (True, [asked, pending]),
        ):
            with self.subTest(resolved=resolved):
                self.assertEqual(self.poll(replied_pr(submitted=False, resolved=resolved)),
                                 (1, [*expected, f"ACTION {REPO}#{NUMBER} @ {HEAD}"]))

    def test_submitted_reply_settles_its_thread_and_comment(self) -> None:
        unresolved = (1, [
            f"unresolved review threads (1): https://github.com/{REPO}/pull/{NUMBER}#discussion_1",
            f"ACTION {REPO}#{NUMBER} @ {HEAD}",
        ])
        self.assertEqual(self.poll(replied_pr(submitted=True, resolved=False)), unresolved)
        github = replied_pr(submitted=True, resolved=True)
        # Resolution can change without changing a comment's updated_at.
        self.assertEqual(self.poll(github), (0, [f"READY {REPO}#{NUMBER} @ {HEAD}"]))
        github.resolved[1] = False
        self.assertEqual(self.poll(github), unresolved)

    def test_an_answered_thread_left_unresolved_blocks_a_stamped_green_pr(self) -> None:
        # dev requires every conversation resolved, so GitHub reports BLOCKED;
        # the open thread is the agent's to resolve, not a wait.
        github = replied_pr(submitted=True, resolved=False)
        github.pr["mergeable_state"] = "blocked"
        self.assertEqual(self.poll(github), (1, [
            f"unresolved review threads (1): https://github.com/{REPO}/pull/{NUMBER}#discussion_1",
            f"ACTION {REPO}#{NUMBER} @ {HEAD}",
        ]))

    def test_a_review_bots_new_thread_is_feedback(self) -> None:
        github = GitHub("BLOCKED")
        github.notes = [{
            **comment("factory-droid", "Bot", "**P2** Buffer too small.", id=5, at="2026-01-02T00:00:00Z"),
            "html_url": f"https://github.com/{REPO}/pull/{NUMBER}#discussion_5",
            "pull_request_review_id": 200, "path": "a.ts", "line": 9, "original_line": 9,
        }]
        github.resolved = {5: False}
        self.assertEqual(self.poll(github), (1, [
            f"thread from factory-droid on a.ts:9: **P2** Buffer too small. https://github.com/{REPO}/pull/{NUMBER}#discussion_5",
            f"unresolved review threads (1): https://github.com/{REPO}/pull/{NUMBER}#discussion_5",
            f"ACTION {REPO}#{NUMBER} @ {HEAD}",
        ]))

    def test_later_runs_revalidate_required_checks_for_free(self) -> None:
        github = GitHub("CLEAN", checks=[check("lint")])
        etag = pr_watch.header(response(github.body(RULES)).split("\r\n\r\n")[0], "etag")
        for expected in (
            [mock.call("api", "--include", RULES, unchanged=False),
             mock.call("api", "--include", PROTECTION, unchanged=False)],
            [mock.call("api", "--include", "-H", f"If-None-Match: {etag}", RULES, unchanged=True)],
        ):
            self.gh.reset_mock()
            self.assertEqual(self.poll(github), (3, [
                "waiting: pending checks (1): test", f"WAIT {REPO}#{NUMBER} @ {HEAD}",
            ]))
            self.assertEqual([c for c in self.gh.call_args_list if c.args[-1] in (RULES, PROTECTION)], expected)

    def test_an_unreadable_required_checks_cache_is_a_miss(self) -> None:
        path = Path(pr_watch.STATE_DIR) / "required" / "o%2Fr%3Adev.json"
        path.parent.mkdir(parents=True)
        path.write_text("{not json")
        self.assertEqual(self.poll(GitHub("CLEAN", checks=[check("lint")])), (3, [
            "waiting: pending checks (1): test", f"WAIT {REPO}#{NUMBER} @ {HEAD}",
        ]))
        self.assertEqual(json.loads(path.read_text())[RULES]["names"], list(REQUIRED))
        self.assertIn(mock.call("api", "--include", RULES, unchanged=False), self.gh.call_args_list)

    def test_stacked_pr_gates_on_its_landing_branchs_checks_that_report(self) -> None:
        github = pr_28805()
        github.stack(STACK_28805)
        self.assertEqual(self.poll(github), (0, [VERCEL_FAILED, f"READY {REPO}#{NUMBER} @ {HEAD}"]))
        github.checks[0] = check("lint", "failure")
        self.assertEqual(self.poll(github), (1, [
            "check-failed lint (gating) https://ci/lint", VERCEL_FAILED,
            f"ACTION {REPO}#{NUMBER} @ {HEAD}",
        ]))

    def test_forks_prs_that_pull_a_branch_into_their_own_copy_are_no_stack(self) -> None:
        for branches, expected in (
            (("dev",), (3, [VERCEL_FAILED, "waiting: pending checks (1): test",
                           f"WAIT {REPO}#{NUMBER} @ {HEAD}"])),
            (STACK_28805, (0, [VERCEL_FAILED, f"READY {REPO}#{NUMBER} @ {HEAD}"])),
        ):
            with self.subTest(branches=branches):
                github = pr_28805()
                github.stack(branches, noise=True)
                self.assertEqual(self.poll(github), expected)

    def test_landing_follows_a_pr_on_the_second_rest_page(self) -> None:
        github = pr_28805()
        github.pr["base"]["ref"] = "stack"
        github.heads["stack"] = [forks("stack")[0]] * 100 + [pr_node("stack", "dev")]
        self.assertEqual(self.poll(github), (0, [VERCEL_FAILED, f"READY {REPO}#{NUMBER} @ {HEAD}"]))
        self.assertTrue(any(c.args[-1].endswith("&page=2") for c in self.gh.call_args_list))

    def test_a_pr_into_its_landing_branch_waits_for_unstarted_required_checks(self) -> None:
        self.assertEqual(self.poll(pr_28805()), (3, [
            VERCEL_FAILED, "waiting: pending checks (1): test", f"WAIT {REPO}#{NUMBER} @ {HEAD}",
        ]))

    def test_a_stack_that_loops_is_an_error(self) -> None:
        github = GitHub("CLEAN")
        github.stack(("a", "b", "a"))
        self.assertEqual(self.poll(github), (2, [
            f"ERROR {REPO}#{NUMBER} GitHub failed: the stack under a loops back to a",
        ]))

    def test_a_landing_branch_that_requires_nothing_makes_every_check_gate(self) -> None:
        github = pr_28805()
        github.pr["base"]["ref"] = FREE
        self.assertEqual(self.poll(github), (1, [
            f"check-failed {VERCEL} (gating) https://vercel.com/factory/delegation-router-dev",
            f"ACTION {REPO}#{NUMBER} @ {HEAD}",
        ]))

    def test_watching_a_stacked_pr_wakes_once_on_its_optional_failure(self) -> None:
        github = pr_28805()
        github.stack(STACK_28805)
        watcher = pr_watch.Watcher(REPO, NUMBER, 300, once=False)
        self.assertEqual(self.poll(github, watcher), (1, [VERCEL_FAILED, f"ACTION {REPO}#{NUMBER} @ {HEAD}"]))
        watcher = pr_watch.Watcher(REPO, NUMBER, 300, once=False)
        self.assertEqual(self.poll(github, watcher), (None, []))
        self.assertEqual(self.poll(github, watcher), (0, [f"READY {REPO}#{NUMBER} @ {HEAD}"]))
        self.assertEqual(self.remote.call_count, 2)

    def test_unapproved_clean_green_pr_waits_for_review(self) -> None:
        self.assertEqual(self.poll(GitHub("CLEAN", approved=False)), (3, [
            "waiting: review: no approval", f"WAIT {REPO}#{NUMBER} @ {HEAD}",
        ]))


class RequiredChecksErrorTest(unittest.TestCase):
    def setUp(self) -> None:
        patcher = mock.patch.object(pr_watch, "BUDGET", pr_watch.Budget())
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_only_a_final_404_or_403_is_cached_as_denied(self) -> None:
        for message, denied in (
            ("gh: Not Found (HTTP 404)", True),
            ("gh: Resource not accessible by integration (HTTP 403)", True),
            ("gh: Bad Gateway (HTTP 502) at /requests/403", False),
        ):
            with self.subTest(message=message), mock.patch.object(pr_watch, "gh", side_effect=pr_watch.GhError(message)):
                if denied:
                    self.assertIn("denied", pr_watch.revalidate(RULES, {}, list))
                else:
                    self.assertRaises(pr_watch.GhError, pr_watch.revalidate, RULES, {}, list)

    def test_an_unparsable_or_empty_graphql_answer_is_a_retryable_error(self) -> None:
        for body in ("<html>502 Bad Gateway</html>", '{"errors": []}', '{"data": null}'):
            with (
                self.subTest(body=body),
                mock.patch.object(pr_watch, "gh", return_value=response(None, resource="graphql").split("\r\n\r\n")[0] + "\r\n\r\n" + body),
            ):
                self.assertRaises(pr_watch.GhError, pr_watch.graphql, pr_watch.THREADS)

    def test_abuse_detection_is_a_rate_limit(self) -> None:
        self.assertTrue(pr_watch.RATE_LIMITED.search(
            "gh: You have triggered an abuse detection mechanism. (HTTP 403)"
        ))


if __name__ == "__main__":
    unittest.main()
