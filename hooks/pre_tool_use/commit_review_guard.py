#!/usr/bin/env python3
"""PreToolUse hook to run CodeRabbit CLI before git push.

Blocks git push when CodeRabbit reports findings.
"""
from __future__ import annotations

import argparse
import re
import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

# add hooks dir to path for rel import
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils import (  # type: ignore
    HookInputError,
    PreToolUseInput,
    exit,
    get_toml_section,
    load_toml,
    read_input_as,
)

HOOK_EVENT_NAME = "PreToolUse"


# ============================================================================
# Configuration
# ============================================================================

@dataclass(slots=True, frozen=True)
class Config:
    max_chars: int
    review_type: str


def _parse_args(argv: list[str]) -> Config:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--config-file", default="", help="Path to TOML config file")
    parser.add_argument("--max-chars", type=int, default=None)
    parser.add_argument("--type", dest="review_type", choices=["all", "committed", "uncommitted"], default=None)
    args = parser.parse_args(argv)

    try:
        config_data = load_toml(args.config_file)
    except OSError as exc:
        exit(
            1,
            text=f"[coderabbit] Config file error: {exc}",
            to_stderr=True,
            hook_event_name=HOOK_EVENT_NAME,
        )
    except Exception as exc:
        exit(
            1,
            text=f"[coderabbit] Config parse error: {exc}",
            to_stderr=True,
            hook_event_name=HOOK_EVENT_NAME,
        )

    config = get_toml_section(config_data, "hooks", "pre_tool_use", "commit_review_guard")
    review_type = args.review_type or config.get("type") or "committed"
    max_chars = args.max_chars if args.max_chars is not None else config.get("max_chars", 6000)

    return Config(
        max_chars=int(max_chars),
        review_type=str(review_type),
    )


# ============================================================================
# Git / CodeRabbit helpers
# ============================================================================

def _run(cmd: list[str], cwd: Path | None = None) -> tuple[int, str, str]:
    result = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def _run_git(args: list[str], cwd: Path) -> tuple[int, str, str]:
    return _run(["git", *args], cwd=cwd)


def _is_git_push_command(command: str) -> bool:
    if not command:
        return False
    return re.search(r"(^|\s)git(\s+[^;&|]+)*\s+push(\s|$)", command) is not None


def _extract_git_cwd(command: str, fallback_cwd: str) -> Path:
    try:
        tokens = shlex.split(command)
    except ValueError:
        return Path(fallback_cwd)

    for i, token in enumerate(tokens):
        if token == "-C" and i + 1 < len(tokens):
            return Path(tokens[i + 1]).expanduser()
        if token.startswith("-C") and len(token) > 2:
            return Path(token[2:]).expanduser()

    return Path(fallback_cwd)


def _get_repo_root(cwd: Path) -> Path | None:
    code, out, _ = _run_git(["rev-parse", "--show-toplevel"], cwd=cwd)
    if code != 0 or not out:
        return None
    return Path(out)


def _get_head_sha(cwd: Path) -> str | None:
    code, out, _ = _run_git(["rev-parse", "HEAD"], cwd=cwd)
    return out if code == 0 and out else None


def _get_branch(cwd: Path) -> str:
    code, out, _ = _run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=cwd)
    return out if code == 0 and out else "detached"


def _get_upstream_commit(cwd: Path) -> str | None:
    code, out, _ = _run_git(["rev-parse", "@{u}"], cwd=cwd)
    return out if code == 0 and out else None


def _get_default_base_branch(cwd: Path) -> str | None:
    code, out, _ = _run_git(["symbolic-ref", "refs/remotes/origin/HEAD"], cwd=cwd)
    if code == 0 and out.startswith("refs/remotes/origin/"):
        return out.split("refs/remotes/origin/", 1)[1]

    for candidate in ("main", "master", "develop"):
        code, _, _ = _run_git(["show-ref", "--verify", f"refs/remotes/origin/{candidate}"], cwd=cwd)
        if code == 0:
            return candidate

    return None


def _resolve_coderabbit_binary() -> str | None:
    return shutil.which("coderabbit") or shutil.which("cr")


# ============================================================================
# Output formatting
# ============================================================================

_NO_FINDINGS_PATTERNS = [
    re.compile(r"(?i)no\s+(issues|findings|problems|concerns)(\s+found)?"),
    re.compile(r"(?i)nothing\s+to\s+report"),
]


def _is_clean(output: str) -> bool:
    stripped = output.strip()
    if not stripped:
        return True
    return any(pattern.search(stripped) for pattern in _NO_FINDINGS_PATTERNS)


def _truncate(text: str, limit: int) -> str:
    if limit <= 0:
        return ""
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 18)] + "... [truncated]"


# ============================================================================
# Main hook logic
# ============================================================================

def _handle_pre_tool_use(hook_input: PreToolUseInput, config: Config) -> None:
    if hook_input.tool_name != "Execute":
        exit(hook_event_name=HOOK_EVENT_NAME)

    command = str(hook_input.tool_input.get("command", ""))
    if not _is_git_push_command(command):
        exit(hook_event_name=HOOK_EVENT_NAME)

    coderabbit_bin = _resolve_coderabbit_binary()
    if coderabbit_bin is None:
        print("[coderabbit] CLI not found. Skipping commit review.")
        exit(hook_event_name=HOOK_EVENT_NAME)
        return
    coderabbit_cmd = coderabbit_bin

    git_cwd = _extract_git_cwd(command, hook_input.cwd)
    repo_root = _get_repo_root(git_cwd)
    if repo_root is None:
        exit(hook_event_name=HOOK_EVENT_NAME)
        return
    repo_root_path = repo_root

    base_commit = _get_upstream_commit(repo_root_path)
    base_branch = None if base_commit else _get_default_base_branch(repo_root_path)

    branch = _get_branch(repo_root_path)

    cmd = [
        coderabbit_cmd,
        "--prompt-only",
        "--no-color",
        "--cwd",
        str(repo_root_path),
        "--type",
        config.review_type,
    ]
    if base_commit:
        cmd.extend(["--base-commit", base_commit])
    elif base_branch:
        cmd.extend(["--base", base_branch])

    code, stdout, stderr = _run(cmd, cwd=repo_root_path)
    combined_output = "\n".join(part for part in [stdout, stderr] if part)

    if code != 0:
        exit(
            decision="deny",
            reason="[coderabbit] CLI failed before push.",
            hook_event_name=HOOK_EVENT_NAME,
        )

    if _is_clean(combined_output):
        exit(hook_event_name=HOOK_EVENT_NAME)

    excerpt = _truncate(combined_output, config.max_chars)
    exit(
        decision="deny",
        reason=(
            "[coderabbit] Issues found before push.\n"
            f"Repo: {repo_root}\n"
            f"Branch: {branch}\n\n"
            f"Excerpt:\n{excerpt}\n\n"
            "Fix critical issues, then re-run push to recheck."
        ),
        hook_event_name=HOOK_EVENT_NAME,
    )


def main():
    config = _parse_args(sys.argv[1:])

    try:
        hook_input = read_input_as(PreToolUseInput)
    except HookInputError as exc:
        exit(
            1,
            text=f"[coderabbit] Hook input error: {exc}",
            to_stderr=True,
            hook_event_name=HOOK_EVENT_NAME,
        )

    _handle_pre_tool_use(hook_input, config)
    exit(hook_event_name=HOOK_EVENT_NAME)


if __name__ == "__main__":
    raise SystemExit(main())
