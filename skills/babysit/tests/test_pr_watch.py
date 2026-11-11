from __future__ import annotations

import contextlib
import importlib.machinery
import importlib.util
import io
import json
import re
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
REPO_ID = "R_1"
FORK_ID = "R_fork"
NUMBER = 7
HEAD = "a" * 40
BASE_OID = "b" * 40
REQUIRED = ("lint", "test")
RATE = {"limit": 5000, "remaining": 4000, "resetAt": "1970-01-01T01:00:00Z", "cost": 1}


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
        "baseRepository": {"id": REPO_ID},
        "baseRef": {"target": {"oid": BASE_OID}, **heads()},
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

# factory-mono#28805 on 2026-11-05: three PRs above dev. Of dev's required
# checks only those whose workflows do not filter on the base report (lint
# here, not test), and a misconfigured Vercel project fails its status on
# every commit.
STACK_28805 = (
    "ainesh/ac-2025-droid-rest",
    "ainesh/ac-2025-droid-cli",
    "ainesh/ac-2025-script-paths",
    "dev",
)
VERCEL = "Vercel – delegation-router-dev"
VERCEL_FAILED = f"check-failed {VERCEL} (optional) https://vercel.com/factory/delegation-router-dev"
CHECKS_28805 = [
    check("lint"),
    check("Validate PR", "CANCELLED"),
    check("Validate PR"),
    {
        "__typename": "StatusContext",
        "context": VERCEL,
        "state": "FAILURE",
        "targetUrl": "https://vercel.com/factory/delegation-router-dev",
    },
]
def pr_node(
    head: str, base: str, head_repo: str | None = REPO_ID, base_repo: str = REPO_ID
) -> dict[str, Any]:
    """An open PR as HEADS lists it; a head_repo of None is a deleted fork."""
    return {
        "headRefName": head,
        "baseRefName": base,
        "headRepository": head_repo and {"id": head_repo},
        "baseRepository": {"id": base_repo},
    }


def heads(*nodes: dict[str, Any], total: int | None = None) -> dict[str, Any]:
    """A ref's open PRs as HEADS answers them."""
    count = len(nodes) if total is None else total
    return {"associatedPullRequests": {"totalCount": count, "nodes": list(nodes)}}


# Forks' PRs that pull o/r's branch into the fork's own copy of it, as GitHub
# lists them on o/r's ref (trycua/cua main on 2026-11-05), and one a fork
# opened into o/r from its own branch of the same name.
def forks(branch: str) -> list[dict[str, Any]]:
    return [
        pr_node(branch, branch, base_repo=FORK_ID),
        pr_node(branch, branch, head_repo=None, base_repo=FORK_ID),
        pr_node(branch, "dev", head_repo=FORK_ID),
    ]


def stacked(
    branches: tuple[str, ...], noise: bool = False
) -> tuple[dict[str, Any], dict[str, Any]]:
    """The PR's baseRef for branches[0] and the stack query's answer for each
    branch above it, each branch the head of an open PR into the next, with
    forks' PRs listed first when noise is set."""
    answers = [
        heads(
            *(forks(b) if noise else []),
            *([pr_node(b, branches[i + 1])] if i + 1 < len(branches) else []),
        )
        for i, b in enumerate(branches)
    ]
    refs = {
        f"refs/heads/{b}": {"repository": {"ref": a}}
        for b, a in zip(branches[1:], answers[1:])
    }
    return {"target": {"oid": BASE_OID}, **answers[0]}, refs


RULES = f"repos/{REPO}/rules/branches/dev"
ETAG = 'W/"1"'
# A branch whose ruleset requires no check.
FREE = "free"


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
    if path == f"repos/{REPO}/rules/branches/{FREE}":
        return "HTTP/2.0 200 OK\r\n\r\n[]"
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

    def once(
        self,
        pr: dict[str, Any],
        notes: dict[str, list[str]] | None = None,
        **refs: Any,
    ) -> tuple[int, list[str]]:
        """Run `pr-watch --once` against pr, with notes as each check run's
        annotation titles by id, and refs answering the stack query for each
        qualified ref name; return its exit code and stdout lines."""
        out = io.StringIO()
        data = {"rateLimit": RATE, "repository": {"pullRequest": pr}}

        def answer(query: str, **variables: Any) -> Any:
            if query == pr_watch.QUERY:
                return data
            if "annotations" in query:
                runs = re.findall(r'node\(id: "([^"]+)"\)', query)
                return {
                    f"r{i}": {
                        "annotations": {
                            "nodes": [{"title": t} for t in (notes or {}).get(run, [])]
                        }
                    }
                    for i, run in enumerate(runs)
                }
            return refs[variables["ref"]]

        with (
            mock.patch.object(pr_watch, "graphql", side_effect=answer),
            contextlib.redirect_stdout(out),
            contextlib.redirect_stderr(io.StringIO()),
            self.assertRaises(SystemExit) as exit,
        ):
            pr_watch.Watcher(REPO, NUMBER, 30, once=True).run()
        return exit.exception.code, out.getvalue().splitlines()

    def test_approved_mergeable_green_pr_is_ready(self) -> None:
        # A failed optional check is listed beside the verdict and never sets it.
        failed = "check-failed optional (optional) https://ci/optional"
        for state, checks, listed in (
            ("CLEAN", None, []),
            ("HAS_HOOKS", None, []),
            ("UNSTABLE", [*map(check, REQUIRED), check("optional", "FAILURE")], [failed]),
        ):
            with self.subTest(state=state):
                code, lines = self.once(pull_request(state, checks=checks))
                self.assertEqual(lines, [*listed, f"READY {REPO}#{NUMBER} @ {HEAD}"])
                self.assertEqual(code, 0)

    def test_failed_optional_check_is_listed_beside_a_wait(self) -> None:
        code, lines = self.once(
            pull_request("BLOCKED", approved=False, checks=[*map(check, REQUIRED), check("prem", "FAILURE")])
        )
        self.assertEqual(code, 3)
        self.assertEqual(lines[0], "check-failed prem (optional) https://ci/prem")
        self.assertEqual(lines[-1], f"WAIT {REPO}#{NUMBER} @ {HEAD}")

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

    def test_a_bots_edit_after_the_agents_response_reopens_its_comment(self) -> None:
        # factory-mono#28661: the QA bot's report from Oct 25 was rewritten to
        # FAILED on Nov 4, after the owner's last reply. A status bot's
        # rewrite stays noise.
        qa = {
            **comment(
                "factory-droid", "Bot", "<!-- qa-report -->\n## QA: FAILED (32 / 34)"
            ),
            "lastEditedAt": "2026-01-03T00:00:00Z",
        }
        reply = {
            **comment("me", "User", f"Fixed.\n\n{pr_watch.AGENT_MARK}"),
            "id": "IC_me",
            "createdAt": "2026-01-02T00:00:00Z",
        }
        status = {
            **comment("github-actions", "Bot", "Deployed"),
            "lastEditedAt": qa["lastEditedAt"],
        }
        ready = f"READY {REPO}#{NUMBER} @ {HEAD}"
        for notes, expected in (
            (
                [qa, reply, status],
                (
                    1,
                    [
                        f"comment from factory-droid: ## QA: FAILED (32 / 34) {qa['url']}",
                        f"ACTION {REPO}#{NUMBER} @ {HEAD}",
                    ],
                ),
            ),
            ([{**qa, "lastEditedAt": None}, reply, status], (0, [ready])),
            ([{**qa, "lastEditedAt": "2026-01-01T12:00:00Z"}, reply], (0, [ready])),
        ):
            with self.subTest(edited=notes[0]["lastEditedAt"]):
                pr = pull_request("CLEAN")
                pr["comments"] = page(notes)
                self.assertEqual(self.once(pr), expected)

    def test_the_e2e_gate_waits_whether_its_status_runs_fail_or_skip(self) -> None:
        # factory-mono#28500 @ a53d9819506 and #30792 @ 49453fb39a0, heads with
        # dev #30901: the plan job's notice says the gate waits, the status
        # jobs skip under their unrendered names, and the required checks they
        # would report never do. Older heads fail the status runs, annotated.
        gate = [pr_watch.GATE_TITLE]
        skipped = check("test${{ needs.plan.outputs.wait }}", "SKIPPED")
        waiting = "waiting: E2E gate (1 checks): runs once approved or labelled e2e:run"
        verdict = f"WAIT {REPO}#{NUMBER} @ {HEAD}"
        review = "waiting: review: review required"
        pending = "waiting: pending checks (1): test"
        for name, approved, checks, notes, expected in (
            (
                "plan notice",
                False,
                [check("lint"), check("plan"), skipped],
                {"run-plan": gate},
                [waiting, review],
            ),
            (
                "failed status run",
                False,
                [check("lint"), check("test", "FAILURE")],
                {"run-test": gate},
                [waiting, review],
            ),
            (
                "no notice",
                False,
                [check("lint"), check("plan"), skipped],
                {},
                [pending, review],
            ),
            (
                "approved",
                True,
                [check("lint"), check("plan"), skipped],
                {"run-plan": gate},
                [pending],
            ),
        ):
            with self.subTest(name):
                pr = pull_request("CLEAN", approved=approved, checks=checks)
                self.assertEqual(self.once(pr, notes=notes), (3, [*expected, verdict]))

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

    def test_stacked_pr_gates_on_its_landing_branchs_checks_that_report(self) -> None:
        # fake_gh reads only dev's ruleset: reading the stack's own branches,
        # which require nothing, fails the test, and would make Vercel gate.
        pr = pull_request("UNSTABLE", checks=list(CHECKS_28805))
        pr["baseRefName"] = STACK_28805[0]
        pr["baseRef"], refs = stacked(STACK_28805)
        self.assertEqual(
            self.once(pr, **refs), (0, [VERCEL_FAILED, f"READY {REPO}#{NUMBER} @ {HEAD}"])
        )
        contexts = pr["commits"]["nodes"][0]["commit"]["statusCheckRollup"]["contexts"]
        contexts["nodes"][0] = check("lint", "FAILURE")
        self.assertEqual(
            self.once(pr, **refs),
            (
                1,
                [
                    "check-failed lint (gating) https://ci/lint",
                    VERCEL_FAILED,
                    f"ACTION {REPO}#{NUMBER} @ {HEAD}",
                ],
            ),
        )

    def test_forks_prs_that_pull_a_branch_into_their_own_copy_are_no_stack(
        self,
    ) -> None:
        # Into dev, a PR waits for dev's unstarted required check; read as a
        # stack, dev "loops back to dev". Stacked, the walk passes the forks'
        # PRs on every branch and lands in dev, where only lint reports.
        pr = pull_request("UNSTABLE", checks=CHECKS_28805)
        pr["baseRef"], refs = stacked(("dev",), noise=True)
        self.assertEqual(
            self.once(pr),
            (
                3,
                [VERCEL_FAILED, "waiting: pending checks (1): test", f"WAIT {REPO}#{NUMBER} @ {HEAD}"],
            ),
        )
        pr["baseRefName"] = STACK_28805[0]
        pr["baseRef"], refs = stacked(STACK_28805, noise=True)
        self.assertEqual(
            self.once(pr, **refs), (0, [VERCEL_FAILED, f"READY {REPO}#{NUMBER} @ {HEAD}"])
        )

    def test_a_branch_heading_more_open_prs_than_one_query_reads_is_an_error(
        self,
    ) -> None:
        pr = pull_request("CLEAN")
        pr["baseRef"] = {"target": {"oid": BASE_OID}, **heads(*forks("dev"), total=101)}
        self.assertEqual(
            self.once(pr),
            (
                2,
                [
                    f"ERROR {REPO}#{NUMBER} GitHub failed: dev heads 101 open PRs, more than one query reads"
                ],
            ),
        )

    def test_a_pr_into_its_landing_branch_waits_for_unstarted_required_checks(
        self,
    ) -> None:
        self.assertEqual(
            self.once(pull_request("UNSTABLE", checks=CHECKS_28805)),
            (
                3,
                [VERCEL_FAILED, "waiting: pending checks (1): test", f"WAIT {REPO}#{NUMBER} @ {HEAD}"],
            ),
        )

    def test_every_query_reads_only_the_target_repository(self) -> None:
        # A token that can read the target PR is the only access a poll needs.
        for query in (pr_watch.QUERY, pr_watch.STACK, pr_watch.MORE_CONTEXTS, pr_watch.MORE_FEEDBACK):
            self.assertEqual(
                set(re.findall(r"repository\(([^)]*)\)", query)) - {"owner: $owner, name: $name"},
                set(),
            )

    def test_a_stack_that_loops_is_an_error(self) -> None:
        pr = pull_request("CLEAN")
        pr["baseRefName"] = "a"
        pr["baseRef"], refs = stacked(("a", "b", "a"))
        code, lines = self.once(pr, **refs)
        self.assertEqual(code, 2)
        self.assertEqual(
            lines[-1],
            f"ERROR {REPO}#{NUMBER} GitHub failed: the stack under a loops back to a",
        )

    def test_a_landing_branch_that_requires_nothing_makes_every_check_gate(
        self,
    ) -> None:
        pr = pull_request("UNSTABLE", checks=list(CHECKS_28805))
        pr["baseRefName"] = FREE
        self.assertEqual(
            self.once(pr),
            (
                1,
                [
                    f"check-failed {VERCEL} (gating) https://vercel.com/factory/delegation-router-dev",
                    f"ACTION {REPO}#{NUMBER} @ {HEAD}",
                ],
            ),
        )

    def watch(
        self, watcher: Any, pr: dict[str, Any], **refs: Any
    ) -> tuple[Any, list[str]]:
        """One watch-mode poll of pr, with refs as in once: its exit code (None
        while it keeps waiting) and stdout lines."""
        out = io.StringIO()
        data = {"rateLimit": RATE, "repository": {"pullRequest": pr}}

        def answer(query: str, **variables: Any) -> Any:
            return data if query == pr_watch.QUERY else refs[variables["ref"]]

        code = None
        with (
            mock.patch.object(pr_watch, "graphql", side_effect=answer),
            contextlib.redirect_stdout(out),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            try:
                watcher.poll()
            except SystemExit as exit:
                code = exit.code
        return code, out.getvalue().splitlines()

    def test_watching_a_stacked_pr_wakes_once_on_its_optional_failure(self) -> None:
        # The Vercel failure wakes the watcher once, as optional; a restart
        # remembers it, settles, and reads READY.
        pr = pull_request("UNSTABLE", checks=list(CHECKS_28805))
        pr["baseRefName"] = STACK_28805[0]
        pr["baseRef"], refs = stacked(STACK_28805)
        watcher = pr_watch.Watcher(REPO, NUMBER, 30, once=False)
        self.assertEqual(
            self.watch(watcher, pr, **refs),
            (1, [VERCEL_FAILED, f"ACTION {REPO}#{NUMBER} @ {HEAD}"]),
        )
        watcher = pr_watch.Watcher(REPO, NUMBER, 30, once=False)
        self.assertEqual(self.watch(watcher, pr, **refs), (None, []))
        self.assertEqual(
            self.watch(watcher, pr, **refs),
            (0, [f"READY {REPO}#{NUMBER} @ {HEAD}"]),
        )

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

    def test_an_unparsable_or_empty_graphql_answer_is_a_retryable_error(self) -> None:
        for body in (
            "<html>502 Bad Gateway</html>",
            '{"errors": []}',
            '{"data": null}',
        ):
            with (
                self.subTest(body=body),
                mock.patch.object(pr_watch, "gh", return_value=body),
            ):
                self.assertRaises(
                    pr_watch.GhError, pr_watch.graphql, "query { viewer { login } }"
                )

    def test_abuse_detection_is_a_rate_limit(self) -> None:
        self.assertTrue(
            pr_watch.RATE_LIMITED.search(
                "gh: You have triggered an abuse detection mechanism. (HTTP 403)"
            )
        )

    @staticmethod
    def limit_reply(remaining: int, reset: int, body: str = "{}") -> str:
        return (
            "HTTP/2.0 200 OK\r\nContent-Type: application/json\r\n"
            f"X-Ratelimit-Remaining: {remaining}\r\nX-Ratelimit-Reset: {reset}\r\n"
            f"\r\n{body}"
        )

    def rate_limit_sleep(self, core: str, graphql: str, now: int = 1_000) -> int:
        replies = [mock.Mock(stdout=core), mock.Mock(stdout=graphql)]
        with (
            mock.patch.object(pr_watch.subprocess, "run", side_effect=replies),
            mock.patch.object(pr_watch.time, "time", return_value=now),
            mock.patch.object(pr_watch.time, "sleep") as sleep,
            contextlib.redirect_stderr(io.StringIO()),
        ):
            pr_watch.wait_for_rate_limit()
        return sleep.call_args.args[0]

    def test_spent_primary_limit_sleeps_until_its_reset(self) -> None:
        reply = self.limit_reply
        self.assertEqual(self.rate_limit_sleep(reply(4000, 2900), reply(0, 1300)), 305)
        self.assertEqual(self.rate_limit_sleep(reply(0, 1100), reply(0, 9000)), 3600)

    def test_headers_outrank_the_rate_limit_body(self) -> None:
        body = '{"resources": {"graphql": {"remaining": 9930, "reset": 4600}}}'
        core = self.limit_reply(7726, 1900, body)
        graphql = self.limit_reply(0, 1300, '{"errors": [{"type": "RATE_LIMIT"}]}')
        self.assertEqual(self.rate_limit_sleep(core, graphql), 305)

    def test_secondary_limit_sleeps_about_a_minute(self) -> None:
        for core, graphql in (
            (self.limit_reply(7974, 4490), self.limit_reply(4999, 4490)),
            ("", ""),
            ("not http", "X-Ratelimit-Remaining: 0\r\n"),
        ):
            with self.subTest(core=core, graphql=graphql):
                self.assertIn(self.rate_limit_sleep(core, graphql), range(50, 71))


class PaceTest(unittest.TestCase):
    """The reset is 3600s after the epoch; every pace below is read at 0."""

    def pace(self, remaining: int, cost: int = 1, now: float = 0) -> int:
        rate = {**RATE, "remaining": remaining, "cost": cost}
        return pr_watch.pace(120, rate, now)

    def test_a_full_budget_polls_at_the_interval(self) -> None:
        self.assertEqual(self.pace(4000), 120)

    def test_a_poll_never_outruns_what_is_left_until_the_reset(self) -> None:
        # 2000 points at 100 a poll last 20 polls: one every 180s.
        self.assertEqual(self.pace(2000, cost=100), 180)

    def test_under_30_percent_left_the_interval_doubles(self) -> None:
        self.assertEqual(self.pace(1499), 240)
        self.assertEqual(self.pace(1500), 120)

    def test_under_5_percent_left_it_sleeps_until_the_reset(self) -> None:
        self.assertEqual(self.pace(249, now=600), 3005)
        self.assertEqual(self.pace(0, now=3599.5), 6)

    def test_a_reset_in_the_past_never_waits_on_it(self) -> None:
        self.assertEqual(self.pace(4000, cost=10, now=7200), 120)

    def test_the_watcher_sleeps_by_the_budget_its_own_poll_read(self) -> None:
        watcher = pr_watch.Watcher(REPO, NUMBER, 120, once=False)
        with (
            mock.patch.object(pr_watch.time, "time", return_value=0),
            mock.patch.object(pr_watch.time, "sleep") as sleep,
            contextlib.redirect_stderr(io.StringIO()) as err,
        ):
            watcher.sleep()
            watcher.rate = {**RATE, "remaining": 1000}
            watcher.sleep()
        self.assertEqual([c.args[0] for c in sleep.call_args_list], [120, 240])
        self.assertIn("GraphQL budget 1000/5000", err.getvalue())

    def test_the_poll_query_reads_its_own_budget(self) -> None:
        self.assertIn("rateLimit { limit remaining resetAt cost }", pr_watch.QUERY)


if __name__ == "__main__":
    unittest.main()
