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
        "user": {"node_id": f"{kind}_{author}", "login": author + ("[bot]" if kind == "Bot" else ""), "type": kind},
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
    """The REST resources, submitted review history and thread resolution on GitHub."""

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

    def gh(self, *args: str, unchanged: bool = False) -> str:
        assert args[0] == "api" and "--include" in args, args
        if args[1] == "graphql":
            assert "owner=o" in args and "name=r" in args and "number=7" in args, args
            # GitHub answers at most 100 threads a page; the cursor is the index after the page.
            start = int(next((a.removeprefix("after=") for a in args if a.startswith("after=")), "0"))
            if f"query={pr_watch.THREADS}" not in args:
                assert f"query={pr_watch.REVIEWS}" in args, args
                rows = self.reviews[start:start + 100]
                end = start + len(rows)
                return response({"data": {"viewer": {"id": "User_me"}, "repository": {"pullRequest": {"reviews": {
                    "pageInfo": {"hasNextPage": end < len(self.reviews), "endCursor": str(end)},
                    "nodes": [{
                        "id": r["node_id"], "databaseId": r["id"], "url": r["html_url"], "state": r["state"],
                        "body": r["body"], "submittedAt": r["submitted_at"], "lastEditedAt": r.get("lastEditedAt"),
                        "commit": {"oid": r["commit_id"]} if r.get("commit_id") else None,
                        "author": {"login": r["user"]["login"]}, "viewerDidAuthor": r["user"]["node_id"] == "User_me",
                        "comments": {"totalCount": sum(c.get("pull_request_review_id") == r["id"] for c in self.notes)},
                    } for r in rows],
                }}}}}, resource="graphql")
            roots = list(self.resolved.items())[start:start + 100]
            end = start + len(roots)
            return response(
                {"data": {"repository": {"pullRequest": {"reviewThreads": {
                    "pageInfo": {"hasNextPage": end < len(self.resolved), "endCursor": str(end) if roots else None},
                    "nodes": [
                        {"isResolved": resolved, "comments": {"nodes": [{"databaseId": root}]}}
                        for root, resolved in roots
                    ],
                }}}}},
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
        conditional = f"{REPO}/pulls" not in url or "/reviews?" in url or "/comments?" in url
        if conditional and f"If-None-Match: {etag}" in args:
            assert unchanged, args
            return response(body, status=304, link=link)
        return out

    def ls_remote(self, args: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        assert args == [
            "git", "-c", "credential.helper=", "-c", "credential.helper=!gh auth git-credential",
            "ls-remote", f"https://github.com/{REPO}.git", "refs/pull/7/head", f"refs/heads/{self.pr['base']['ref']}", "refs/heads/feat",
        ], args
        head = self.pr["head"]["sha"]
        return subprocess.CompletedProcess(args, 0, f"{head}\trefs/pull/7/head\n{head}\trefs/heads/feat\n{self.pr['base']['sha']}\trefs/heads/{self.pr['base']['ref']}\n", "")

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

RISK_MARK = "<!-- factory-pr-risk -->"


def risk_notice(state: str) -> str:
    return (
        f"{RISK_MARK}\n<!-- factory-pr-risk-state: {state.lower()} {HEAD} -->\n"
        f"## Risk Assessment: {state}\n\nAssessing head `{HEAD[:12]}`."
    )


def risk_assessment(
    scored: str, verdict: str, *, at: str = "2026-01-01T00:00:00Z", marker: bool = True
) -> dict[str, Any]:
    """factory-mono's sticky risk comment, as it is rewritten on each push: the scored head in a hidden marker, or
    in the visible line of a comment published before the marker."""
    head = (
        f"<!-- factory-pr-risk-scored-head: {scored} -->\n\n"
        if marker
        else f"\n**`skill-v4`**\n\nScored head `{scored}`; trusted base `{BASE_OID[:12]}`.\n\n"
    )
    body = (
        f"{RISK_MARK}\n## Risk Assessment: {verdict}\n{head}| Score | Value |\n| --- | --- |\n\n"
        "- Human review is required: `a.ts:12` changes teardown.\n"
        "- No concrete regression was established.\n"
        "- A third point stays in the comment.\n\n<details><summary>Why</summary>\n\n- Rubric detail.\n</details>"
    )
    return {**comment("github-actions", "Bot", body, id=9, at="2026-01-01T00:00:00Z"), "updated_at": at}


RISK_LINE = (
    f"risk-assessment Human review needed at {HEAD[:12]}: Human review is required: `a.ts:12` changes "
    f"teardown. No concrete regression was established. https://github.com/{REPO}/pull/{NUMBER}#issuecomment-9"
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
                    watcher.rest.save()
            except SystemExit as exit:
                code = exit.code
        return code, out.getvalue().splitlines()

    def test_once_on_a_fresh_machine_prints_its_verdict(self) -> None:
        github = GitHub("CLEAN")
        github.pr |= {"state": "closed", "merged_at": "2026-11-17T00:00:00Z"}
        with mock.patch.object(pr_watch, "STATE_DIR", Path(pr_watch.STATE_DIR) / "fresh"):
            code, out = self.poll(github)
        self.assertEqual((code, out[-1].split()[0]), (0, "MERGED"))

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

    def test_only_a_stale_description_marker_needs_refresh(self) -> None:
        github = GitHub("CLEAN")
        ready = (0, [f"READY {REPO}#{NUMBER} @ {HEAD}"])
        stale = f"<!-- pr-desc-base: {BASE_OID} -->"
        current = f"<!-- pr-desc-base: {HEAD} -->"
        for body, expected in (
            ("A hand-written upstream description.", ready),
            (stale, (1, [f"body-stale: description last reconciled at {BASE_OID[:7]}", f"ACTION {REPO}#{NUMBER} @ {HEAD}"])),
            (f"{stale}\r\n{current}", ready),
        ):
            with self.subTest(body=body):
                github.pr["body"] = body
                self.assertEqual(self.poll(github), expected)

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

    def with_comments(self, *comments: Any) -> GitHub:
        github = GitHub("CLEAN")
        github.comments = list(comments)
        return github

    def test_a_bots_edit_after_the_agents_response_reopens_its_comment(self) -> None:
        # factory-mono#28661: a QA report was edited to FAILED after our reply.
        qa = comment("factory-droid", "Bot", "<!-- qa-report -->\n## QA: FAILED (32 / 34)")
        reply = comment("me", "User", "Fixed.", id=2, at="2026-01-02T00:00:00Z")
        status = {**comment("github-actions", "Bot", "Deployed", id=3), "updated_at": "2026-01-03T00:00:00Z"}
        for edited, expected in (
            ("2026-01-03T00:00:00Z", (1, [
                f"comment from factory-droid: ## QA: FAILED (32 / 34) {qa['html_url']}",
                f"ACTION {REPO}#{NUMBER} @ {HEAD}",
            ])),
            (qa["created_at"], (0, [f"READY {REPO}#{NUMBER} @ {HEAD}"])),

        ):
            with self.subTest(edited=edited):
                github = GitHub("CLEAN")
                github.comments = [{**qa, "updated_at": edited}, reply, status]
                self.assertEqual(self.poll(github), expected)

    def test_only_feedback_after_the_viewers_last_word_holds_ready(self) -> None:
        question = comment("pr-author", "User", "Which revision?", id=5)
        github = self.with_comments(question)
        github.pr["user"] = question["user"]
        watcher = pr_watch.Watcher(REPO, NUMBER, 300, once=False)
        self.assertEqual(self.poll(github, watcher)[0], 1)
        self.assertEqual(self.poll(github, watcher), (None, []))
        self.assertEqual(self.poll(github)[0], 1)  # Delivery was not an answer.
        reply = comment("me", "User", "The revision on dev.", id=6)
        github.reviews.append({**reply, "state": "COMMENTED", "submitted_at": "2026-01-02T00:00:00Z"})
        self.assertEqual(self.poll(github)[0], 0)
        review = github.reviews[0]
        review.update(body="Why was it reverted?", lastEditedAt="2026-01-03T00:00:00Z")
        code, lines = self.poll(github, watcher)
        self.assertEqual(code, 1)
        self.assertIn("Why was it reverted?", lines[0])
        self.assertEqual(self.poll(github)[0], 1)

    def test_rate_limited_once_returns_wait_without_sleeping(self) -> None:
        github = GitHub("CLEAN")
        with mock.patch.object(github, "gh", side_effect=pr_watch.GhError("API rate limit exceeded")):
            code, lines = self.poll(github)
        self.assertEqual(code, 3)
        self.assertTrue(lines[-1].startswith("WAIT o/r#7 GitHub rate limited"))

    def test_once_lists_the_heads_risk_assessment_without_setting_the_verdict(self) -> None:
        scored = risk_assessment(HEAD[:12], "Human review needed")
        for body, listed in (
            (scored["body"], [RISK_LINE]),
            (risk_assessment(HEAD[:12], "Human review needed", marker=False)["body"], [RISK_LINE]),
            (risk_assessment(HEAD, "Human review needed")["body"], [RISK_LINE]),
            (risk_notice("Waiting"), []),
            (risk_notice("Running"), []),
            (risk_assessment("c" * 12, "Human review needed")["body"], []),
        ):
            with self.subTest(body=body[:60]):
                github = GitHub("CLEAN")
                github.comments = [{**scored, "body": body}, comment("github-actions", "Bot", "Deployed", id=3)]
                self.assertEqual(self.poll(github), (0, [*listed, f"READY {REPO}#{NUMBER} @ {HEAD}"]))

    def test_the_assessment_is_no_comment_event_when_a_feedback_bot_posts_it(self) -> None:
        # factory-mono posts it as factory-droid, whose other comments are feedback.
        for body, listed in (
            (risk_notice("Running"), []),
            (risk_assessment(HEAD, "Human review needed")["body"], [RISK_LINE]),
        ):
            with self.subTest(body=body[:60]):
                github = GitHub("CLEAN")
                github.comments = [comment("factory-droid", "Bot", body, id=9)]
                self.assertEqual(self.poll(github), (0, [*listed, f"READY {REPO}#{NUMBER} @ {HEAD}"]))

    def test_a_watcher_wakes_once_per_scored_head_and_verdict_of_the_rewritten_assessment(self) -> None:
        github = GitHub("CLEAN")
        github.comments = [{**risk_assessment(HEAD[:12], "Human review needed"), "body": risk_notice("Waiting")}]
        watcher = pr_watch.Watcher(REPO, NUMBER, 300, once=False)
        self.assertEqual(self.poll(github, watcher), (None, []))
        # The same comment, rewritten in place once the head is scored.
        github.comments = [risk_assessment(HEAD[:12], "Human review needed", at="2026-01-02T00:00:00Z")]
        self.assertEqual(self.poll(github, watcher), (1, [RISK_LINE, f"ACTION {REPO}#{NUMBER} @ {HEAD}"]))
        # A restarted watcher holds it, though the agent never replied on the PR.
        watcher = pr_watch.Watcher(REPO, NUMBER, 300, once=False)
        self.assertEqual(self.poll(github, watcher), (None, []))
        self.assertEqual(self.poll(github, watcher), (0, [f"READY {REPO}#{NUMBER} @ {HEAD}"]))
        github.comments = [risk_assessment(HEAD[:12], "Approve", at="2026-01-03T00:00:00Z")]
        watcher = pr_watch.Watcher(REPO, NUMBER, 300, once=False)
        code, lines = self.poll(github, watcher)
        self.assertEqual(code, 1)
        self.assertTrue(lines[0].startswith(f"risk-assessment Approve at {HEAD[:12]}: "), lines)
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

    def test_submitted_reply_settles_only_its_thread(self) -> None:
        unresolved = (1, [
            f"unresolved review threads (1): https://github.com/{REPO}/pull/{NUMBER}#discussion_1",
            f"ACTION {REPO}#{NUMBER} @ {HEAD}",
        ])
        pending = replied_pr(submitted=True, resolved=False)
        self.assertTrue(self.poll(pending)[1][0].startswith("comment from someone: Why?"))
        pending.comments = []
        self.assertEqual(self.poll(pending), unresolved)
        github = replied_pr(submitted=True, resolved=True)
        github.comments = []
        # Resolution can change without changing a comment's updated_at.
        self.assertEqual(self.poll(github), (0, [f"READY {REPO}#{NUMBER} @ {HEAD}"]))
        github.resolved[1] = False
        self.assertEqual(self.poll(github), unresolved)

    def test_unread_resolution_never_inherits_a_cached_ready(self) -> None:
        github = replied_pr(submitted=True, resolved=True)
        github.comments = []
        self.assertEqual(self.poll(github)[0], 0)
        github.resolved[1] = False
        read = pr_watch.graphql

        def unread_threads(query: str, **variables: Any) -> Any:
            if query == pr_watch.THREADS:
                raise pr_watch.GhError("unavailable")
            return read(query, **variables)

        for blocked in (True, False):
            with mock.patch.object(pr_watch.BUDGET, "low", return_value=blocked), mock.patch.object(
                pr_watch, "graphql", side_effect=unread_threads
            ):
                code, lines = self.poll(github)
            self.assertEqual(code, 3)
            self.assertIn("waiting: review thread resolution unavailable", lines)
        self.assertEqual(self.poll(github)[0], 1)

    def test_an_answered_thread_left_unresolved_blocks_a_stamped_green_pr(self) -> None:
        # dev requires every conversation resolved, so GitHub reports BLOCKED;
        # the open thread is the agent's to resolve, not a wait.
        github = replied_pr(submitted=True, resolved=False)
        github.comments = []
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

    def test_fix_pushes_not_commits_or_bot_replies_close_both_watch_modes(self) -> None:
        github = GitHub("CLEAN")
        github.pr["user"] = {"login": "me", "type": "User"}
        original, fix = "c" * 40, "d" * 40
        ref = f"refs/heads/{github.pr['head']['ref']}"
        pushes = [{"after": sha, "ref": ref, "actor": {"login": "me"}, "activity_type": "push",
                   "timestamp": f"2026-01-{day:02}T00:59:00Z"}
                  for day, sha in enumerate((original, fix, HEAD), 2)]
        resource = f"repos/{REPO}/activity?ref={pr_watch.quote(ref, safe='')}&per_page=100"
        body = github.body
        github.body = lambda url: pushes if url == resource else body(url)

        def finding(n, sha, day, fixed=""):
            at = f"2026-01-{day:02}T01:00:00Z"
            github.reviews.append({**comment("reviewer", "Bot", "", id=n, at=at),
                                   "state": "COMMENTED", "submitted_at": at, "commit_id": sha})
            root = {**comment("reviewer", "Bot", "Bad rounding.", id=n, at=at),
                    "path": "a.py", "pull_request_review_id": n, "original_commit_id": sha}
            github.notes.append(root)
            github.resolved[n] = bool(fixed)
            if fixed:
                github.notes.append({**root, **comment("me", "User", f"Fixed in {fixed}.\n\n{pr_watch.AGENT_MARK}",
                                                       id=n+100, at=at), "in_reply_to_id": n})

        finding(1, original, 2, f"{'e'*9}, tests in {fix[:9]}")
        finding(2, fix, 3)
        finding(3, fix, 3, HEAD[:9])
        # A two-commit fix, two reviews on one tip, and a human push do not close the loop.
        self.assertEqual(self.poll(github)[1][-1].split()[0], "ACTION")
        finding(4, HEAD, 4)
        pushes[-1]["actor"]["login"] = "other"
        self.assertEqual(self.poll(github)[1][-1].split()[0], "ACTION")
        pushes[-1]["actor"]["login"] = "me"
        with mock.patch.object(pr_watch, "ground_up_complete", return_value=False):
            for once in (True, False, True):
                code, lines = self.poll(github, pr_watch.Watcher(REPO, NUMBER, 300, once))
                self.assertEqual(code, 1)
                self.assertEqual(len(lines), 1)
                self.assertTrue(lines[0].startswith(f"REVIEW_STOP {REPO}#{NUMBER} @ {HEAD}"))
            # The watcher wakes once; a foreground recheck never hides the stop.
            self.assertEqual(self.poll(github, pr_watch.Watcher(REPO, NUMBER, 300, False)), (None, []))
            pushes.clear()
            self.assertTrue(self.poll(github)[1][0].startswith("REVIEW_STOP "))
            # Written dispositions can resolve the remaining threads without a patch.
            github.resolved.update({2: True, 4: True})
            self.assertEqual(self.poll(github), (0, [f"READY {REPO}#{NUMBER} @ {HEAD}"]))
            github.comments.append(risk_assessment(HEAD[:12], "Human review needed"))
            self.assertEqual(self.poll(github), (0, [RISK_LINE, f"READY {REPO}#{NUMBER} @ {HEAD}"]))
        github.resolved[4] = False
        with mock.patch.object(pr_watch, "ground_up_complete", return_value=True):
            self.assertEqual(self.poll(github)[1][-1].split()[0], "ACTION")

    def test_only_completed_dossier_for_this_pr_and_head_authorizes_fixing(self) -> None:
        reviewed, fix, later = "1" * 40, "2" * 40, HEAD
        # reviewed <- fix <- later; BASE_OID is unrelated.
        history = {(reviewed, fix), (reviewed, later), (fix, later)}

        with tempfile.TemporaryDirectory() as tmp:
            def git(argv, **_):
                if argv[1:3] == ["merge-base", "--is-ancestor"]:
                    old, new = argv[3:5]
                    return subprocess.CompletedProcess(argv, 0 if old == new or (old, new) in history else 1)
                return subprocess.CompletedProcess(argv, 0, tmp + "\n")

            self.remote.side_effect = git
            dossier = Path(tmp) / ".agents/review.md"
            dossier.parent.mkdir()
            text = f"# PR {NUMBER} — Change\n\nrepo: {REPO}\nreviewed_head: {HEAD}\nmode: ground-up\nverdict: COMMENT\n\n## Reference design\nOne owner.\n"
            for old, new in ((HEAD, BASE_OID), (REPO, "other/repo"), ("PR 7", "PR 71"),
                             ("COMMENT", "not yet issued"), ("One owner.", "none")):
                dossier.write_text(text.replace(old, new))
                self.assertFalse(pr_watch.ground_up_complete(REPO, NUMBER, HEAD), (old, new))
            dossier.write_text(text)
            self.assertTrue(pr_watch.ground_up_complete(REPO, NUMBER, HEAD))
            # A follow-up on a ground-up review renames the mode and keeps the reference design.
            dossier.write_text(text.replace("mode: ground-up", "mode: follow-up"))
            self.assertTrue(pr_watch.ground_up_complete(REPO, NUMBER, HEAD))
            # Fix commits on a reviewed head need no second pass, until a bot
            # finds something on one of them.
            dossier.write_text(text.replace(HEAD, reviewed))
            self.assertTrue(pr_watch.ground_up_complete(REPO, NUMBER, later, {reviewed}))
            self.assertFalse(pr_watch.ground_up_complete(REPO, NUMBER, later, {reviewed, fix}))
            self.assertFalse(pr_watch.ground_up_complete(REPO, NUMBER, BASE_OID))

    def test_bot_owned_pr_counts_only_actual_post_review_push_tips(self) -> None:
        github = GitHub("CLEAN")
        github.pr["user"] = {"login": "delegations[bot]", "type": "Bot"}
        source = github.pr["head"]
        ref = f"refs/heads/{source['ref']}"
        shas = ["1" * 40, "2" * 40, "3" * 40, HEAD]
        activity = []
        for i, sha in enumerate(shas, 1):
            at = f"2026-01-{i:02}T01:00:00Z"
            github.reviews.append({**comment("droid", "Bot", "", id=i), "commit_id": sha,
                                   "state": "COMMENTED", "submitted_at": at})
            github.notes.append({**comment("droid", "Bot", "Incorrect.", id=i, at=at),
                                 "pull_request_review_id": i, "path": "f.py", "line": 1})
            github.resolved[i] = i != len(shas)
            activity.append({"ref": ref, "actor": github.pr["user"], "activity_type": "push",
                             "after": sha, "timestamp": f"2026-01-{i:02}T00:00:00Z"})
        # The second reviewed SHA was inside a push, never itself a pushed tip.
        del activity[1]
        activity[-1]["actor"] = {"login": "someone-else"}
        body = github.body
        github.body = lambda url: activity if "/activity?" in url else body(url)
        self.assertEqual(self.poll(github)[1][-1].split()[0], "ACTION")
        activity[-1]["actor"] = github.pr["user"]
        with mock.patch.object(pr_watch, "ground_up_complete", return_value=False):
            self.assertTrue(self.poll(github)[1][0].startswith("REVIEW_STOP "))

    def test_a_late_submitted_review_drafted_on_an_older_commit_is_feedback(self) -> None:
        # A pending review's comments keep their drafting time and are outdated
        # the moment it is submitted (factory-mono#27809: drafted Oct 22 on an
        # older commit, submitted with an approval Nov 11, after the agent's reply).
        github = GitHub("BLOCKED")
        github.comments = [comment("me", "User", f"Pushed.\n\n{pr_watch.AGENT_MARK}", id=3, at="2026-01-02T00:00:00Z")]
        github.notes = [{
            **comment("jerry", "User", "Guard this.", id=5, at="2025-10-22T00:00:00Z"),
            "updated_at": "2026-01-03T00:00:00Z",
            "html_url": f"https://github.com/{REPO}/pull/{NUMBER}#discussion_5",
            "pull_request_review_id": 200, "path": "a.ts", "line": None, "original_line": 9,
        }]
        github.resolved = {5: False}
        self.assertEqual(self.poll(github), (1, [
            f"thread from jerry on a.ts:9: Guard this. https://github.com/{REPO}/pull/{NUMBER}#discussion_5",
            f"unresolved review threads (1): https://github.com/{REPO}/pull/{NUMBER}#discussion_5",
            f"ACTION {REPO}#{NUMBER} @ {HEAD}",
        ]))

    def test_a_reported_thread_outdated_by_a_push_does_not_wake_again(self) -> None:
        github = GitHub("BLOCKED")
        github.notes = [{
            **comment("someone", "User", "Rename this.", id=5, at="2026-01-02T00:00:00Z"),
            "html_url": f"https://github.com/{REPO}/pull/{NUMBER}#discussion_5",
            "path": "a.ts", "line": 9, "original_line": 9,
        }]
        github.resolved = {5: False}
        watcher = pr_watch.Watcher(REPO, NUMBER, 300, once=False)
        self.assertEqual(self.poll(github, watcher)[0], 1)
        github.notes[0]["line"] = None
        self.assertEqual(self.poll(github, pr_watch.Watcher(REPO, NUMBER, 300, once=False)), (None, []))

    def test_reopened_reported_thread_wakes_again_without_a_comment_edit(self) -> None:
        github = replied_pr(submitted=False, resolved=False)
        github.comments.clear()
        github.reviews.clear()
        github.notes.pop()
        for resolved, wake in [(False, True), (False, False), (True, False), (False, True)]:
            github.resolved[1] = resolved
            watcher = pr_watch.Watcher(REPO, NUMBER, 300, once=False)
            _, lines = self.poll(github, watcher)
            self.assertEqual(any(line.startswith("thread from") for line in lines), wake)

    def test_every_threads_resolution_is_read_past_the_first_page(self) -> None:
        # factory-mono#27387 has 179 threads, all resolved; a one-page read left
        # 79 of them unresolved and woke the owner on each.
        github = GitHub("CLEAN")
        github.notes = [{
            **comment("someone", "User", f"Nit {i}.", id=i, at="2026-01-02T00:00:00Z"),
            "html_url": f"https://github.com/{REPO}/pull/{NUMBER}#discussion_{i}",
            "path": "a.ts", "line": i, "original_line": i,
        } for i in range(1, 180)]
        github.resolved = dict.fromkeys(range(1, 180), True)
        self.assertEqual(self.poll(github), (0, [f"READY {REPO}#{NUMBER} @ {HEAD}"]))

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


class ProxyReadTest(unittest.TestCase):
    def test_standing_watcher_survives_a_failed_poll_then_alternating_407s(self) -> None:
        github = GitHub("CLEAN")
        calls: list[list[str]] = []

        def run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
            calls.append(command)
            # The first read exhausts all five attempts. Thereafter every other call fails.
            if len(calls) <= 5 or len(calls) % 2 == 0:
                message = "CONNECT tunnel failed, response 407" if command[0] == "git" else "Proxy Authentication Required"
                return subprocess.CompletedProcess(command, 1, "", message)
            if command[0] == "git":
                return github.ls_remote(command)
            return subprocess.CompletedProcess(command, 0, github.gh(*command[1:], unchanged=True), "")

        with tempfile.TemporaryDirectory() as root, mock.patch.object(pr_watch, "STATE_DIR", Path(root)):
            watcher = pr_watch.Watcher(REPO, NUMBER, 300, once=False)
            out = io.StringIO()
            with (
                mock.patch.object(pr_watch.subprocess, "run", side_effect=run),
                mock.patch.object(pr_watch.time, "sleep"),
                mock.patch.object(pr_watch, "BUDGET", pr_watch.Budget()),
                mock.patch.object(pr_watch.time, "time", return_value=NOW),
                mock.patch.object(watcher, "sleep", side_effect=[None, None, AssertionError("third poll did not reach READY")]) as between_polls,
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()),
                self.assertRaises(SystemExit) as exit,
            ):
                watcher.run()
        self.assertEqual((exit.exception.code, out.getvalue().splitlines()[-1]), (0, f"READY {REPO}#{NUMBER} @ {HEAD}"))
        self.assertEqual(between_polls.call_count, 2)  # failed poll, then first green snapshot
        self.assertEqual(calls[:5], [calls[0]] * 5)
        self.assertEqual(calls[5::2], calls[6::2])  # retry each failed read, including ls-remote
        self.assertIn("git", [command[0] for command in calls])


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
