#!/usr/bin/env python3
"""PreToolUse hook: run CodeRabbit CLI before `git push`.

This hook blocks pushes when the CodeRabbit CLI reports findings.
It detects findings structurally (file/line/type blocks) instead of relying on
fragile "no issues found" phrasing.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

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
    timeout_sec: float | None
    on_cli_failure: Literal["deny", "allow"]
    cache_dir: Path | None
    cache_ttl_sec: int


def _parse_args(argv: list[str]) -> Config:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--config-file", default="", help="Path to TOML config file")
    parser.add_argument("--max-chars", type=int, default=None)
    parser.add_argument("--type", dest="review_type", choices=["all", "committed", "uncommitted"], default=None)
    parser.add_argument("--timeout-sec", type=float, default=None)
    parser.add_argument("--on-cli-failure", choices=["deny", "allow"], default=None)
    parser.add_argument("--cache-dir", default=None)
    parser.add_argument("--cache-ttl-sec", type=int, default=None)
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

    raw_timeout = args.timeout_sec if args.timeout_sec is not None else config.get("timeout_sec")
    timeout_sec: float | None
    if isinstance(raw_timeout, (int, float)):
        timeout_sec = float(raw_timeout)
        if timeout_sec <= 0:
            timeout_sec = None
    else:
        timeout_sec = None

    raw_failure = args.on_cli_failure or config.get("on_cli_failure") or "deny"
    on_cli_failure: Literal["deny", "allow"] = "allow" if str(raw_failure) == "allow" else "deny"

    raw_cache_dir = args.cache_dir if args.cache_dir is not None else config.get("cache_dir")
    cache_dir = Path(str(raw_cache_dir)).expanduser() if raw_cache_dir else None

    raw_ttl = args.cache_ttl_sec if args.cache_ttl_sec is not None else config.get("cache_ttl_sec")
    cache_ttl_sec = int(raw_ttl) if isinstance(raw_ttl, int) and raw_ttl >= 0 else 6 * 60 * 60

    return Config(
        max_chars=int(max_chars),
        review_type=str(review_type),
        timeout_sec=timeout_sec,
        on_cli_failure=on_cli_failure,
        cache_dir=cache_dir,
        cache_ttl_sec=cache_ttl_sec,
    )


# ============================================================================
# Git / CodeRabbit helpers
# ============================================================================

def _run(cmd: list[str], cwd: Path | None = None, timeout_sec: float | None = None) -> tuple[int, str, str, bool]:
    try:
        result = subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
        )
        return result.returncode, result.stdout, result.stderr, False
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        return 124, stdout, stderr, True


def _run_git(args: list[str], cwd: Path) -> tuple[int, str, str]:
    code, out, err, _ = _run(["git", *args], cwd=cwd)
    return code, out.strip(), err.strip()


_SHELL_SEPARATORS = {"&&", ";", "|", "||", "&"}


def _is_git_push_command(command: str) -> bool:
    if not command:
        return False
    try:
        tokens = shlex.split(command)
    except ValueError:
        return re.search(r"(^|\s)git(\s+[^;&|]+)*\s+push(\s|$)", command) is not None

    last_sep = -1
    for i, tok in enumerate(tokens):
        if tok in _SHELL_SEPARATORS:
            last_sep = i
            continue
        if tok != "git":
            continue

        # `VAR=... git push` prefixes are common; treat them as part of the command start.
        prefix = tokens[last_sep + 1 : i]
        if prefix and not all(re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", p) for p in prefix):
            continue

        j = i + 1
        while j < len(tokens) and tokens[j] not in _SHELL_SEPARATORS:
            if tokens[j] == "push":
                return True
            j += 1
    return False


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

    # Best-effort: `(cd /path && git push)` style commands.
    m = re.search(
        r"(?:^|\()\s*cd\s+(?P<dir>\"[^\"]+\"|'[^']+'|[^;&|]+)\s*(?:&&|;)\s*git\b",
        command,
    )
    if m:
        raw_dir = m.group("dir").strip()
        if (raw_dir.startswith("\"") and raw_dir.endswith("\"")) or (raw_dir.startswith("'") and raw_dir.endswith("'")):
            raw_dir = raw_dir[1:-1]
        return Path(raw_dir).expanduser()

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


def _rev_parse(cwd: Path, ref: str) -> str | None:
    code, out, _ = _run_git(["rev-parse", ref], cwd=cwd)
    return out if code == 0 and out else None


def _count_commits(cwd: Path, base: str, head: str) -> int | None:
    code, out, _ = _run_git(["rev-list", "--count", f"{base}..{head}"], cwd=cwd)
    if code != 0:
        return None
    try:
        return int(out)
    except ValueError:
        return None


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
@dataclass(slots=True, frozen=True)
class Finding:
    file: str
    line: str | None = None
    type: str | None = None


_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
_KV_RE = re.compile(r"^\s*(?P<key>[A-Za-z][A-Za-z0-9 _/-]{0,64})\s*:\s*(?P<value>.*)\s*$")
_SEPARATOR_RE = re.compile(r"^\s*={8,}\s*$")


def _strip_ansi(text: str) -> str:
    return _ANSI_RE.sub("", text)


def _normalize_output(stdout: str, stderr: str) -> str:
    combined = "\n".join(part for part in (stdout, stderr) if part)
    combined = combined.replace("\r\n", "\n").replace("\r", "\n")
    return _strip_ansi(combined)


def _canonical_key(raw: str) -> str | None:
    k = raw.strip().lower()
    if k == "file":
        return "file"
    if k == "line":
        return "line"
    if k == "type":
        return "type"
    if k in {"prompt", "prompt for ai agent", "prompt for ai assistant"}:
        return "prompt"
    return None


def _clean_file_ref(value: str) -> str:
    v = value.strip()
    if v.startswith("@"):
        v = v[1:]
    if (v.startswith("\"") and v.endswith("\"")) or (v.startswith("'") and v.endswith("'")) or (v.startswith("`") and v.endswith("`")):
        v = v[1:-1]
    return v.strip()


def _looks_pathish(value: str) -> bool:
    v = value.strip()
    if not v or len(v) > 4096:
        return False
    if v.startswith("http://") or v.startswith("https://"):
        return False
    return ("/" in v) or ("\\" in v)


def _summarize_path(file_ref: str, repo_root: Path) -> str:
    p = Path(file_ref)
    if p.is_absolute():
        try:
            return str(p.relative_to(repo_root))
        except ValueError:
            return str(p)
    return file_ref


def _finalize_finding(record: dict[str, str], repo_root: Path) -> Finding | None:
    raw_file = record.get("file")
    if not raw_file:
        return None
    file_ref = _clean_file_ref(raw_file)
    if not _looks_pathish(file_ref):
        return None

    has_extra_signal = any(k in record for k in ("line", "type", "prompt"))
    if not has_extra_signal:
        return None

    return Finding(
        file=_summarize_path(file_ref, repo_root),
        line=record.get("line"),
        type=record.get("type"),
    )


def _parse_findings(text: str, repo_root: Path) -> tuple[Finding, ...]:
    lines = text.splitlines()
    findings: list[Finding] = []

    current: dict[str, str] = {}

    def flush() -> None:
        nonlocal current
        f = _finalize_finding(current, repo_root)
        if f is not None:
            findings.append(f)
        current = {}

    for line in lines:
        if _SEPARATOR_RE.match(line):
            continue

        m = _KV_RE.match(line)
        if not m:
            continue

        key = _canonical_key(m.group("key"))
        if key is None:
            continue

        value = m.group("value")
        if key == "file":
            flush()
            current["file"] = value
            continue

        if not current:
            continue

        if key == "prompt":
            current["prompt"] = "1"  # marker only; prompt content is multi-line
        else:
            current[key] = value

    flush()

    if findings:
        return tuple(findings)

    # Fallback: detect `@path ... lines X - Y` patterns.
    fallback: list[Finding] = []
    path_re = re.compile(r"@(?P<file>[A-Za-z0-9_./\\-]+)")
    line_re = re.compile(r"(?i)lines?\s+(?P<a>\d+)\s*(?:-|to)\s*(?P<b>\d+)")
    for raw in lines:
        pm = path_re.search(raw)
        lm = line_re.search(raw)
        if not (pm and lm):
            continue
        file_ref = _clean_file_ref(pm.group("file"))
        if not _looks_pathish(file_ref):
            continue
        fallback.append(
            Finding(
                file=_summarize_path(file_ref, repo_root),
                line=f"{lm.group('a')} to {lm.group('b')}",
            )
        )
    return tuple(fallback)


def _truncate(text: str, limit: int) -> str:
    if limit <= 0:
        return ""
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 18)] + "... [truncated]"


def _summarize_findings(findings: tuple[Finding, ...], max_items: int = 10) -> str:
    lines: list[str] = []
    for f in findings[:max_items]:
        suffix = ""
        if f.line and f.type:
            suffix = f":{f.line} ({f.type})"
        elif f.line:
            suffix = f":{f.line}"
        elif f.type:
            suffix = f" ({f.type})"
        lines.append(f"- {f.file}{suffix}")
    if len(findings) > max_items:
        lines.append(f"- ... and {len(findings) - max_items} more")
    return "\n".join(lines)


@dataclass(slots=True, frozen=True)
class CacheEntry:
    head_sha: str
    base_sha: str
    review_type: str
    status: Literal["clean", "findings"]
    timestamp: float


def _cache_file(cache_dir: Path, repo_root: Path) -> Path:
    repo_id = hashlib.sha256(str(repo_root).encode("utf-8")).hexdigest()[:16]
    return cache_dir / f"coderabbit-{repo_id}.json"


def _load_cache(path: Path) -> CacheEntry | None:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(raw, dict):
        return None

    try:
        head_sha = str(raw.get("head_sha", ""))
        base_sha = str(raw.get("base_sha", ""))
        review_type = str(raw.get("review_type", ""))
        status = str(raw.get("status", ""))
        timestamp = float(raw.get("timestamp", 0.0))
    except Exception:
        return None

    if not head_sha or not base_sha or not review_type:
        return None
    if status not in {"clean", "findings"}:
        return None
    return CacheEntry(head_sha=head_sha, base_sha=base_sha, review_type=review_type, status=status, timestamp=timestamp)


def _store_cache(path: Path, entry: CacheEntry) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "head_sha": entry.head_sha,
                    "base_sha": entry.base_sha,
                    "review_type": entry.review_type,
                    "status": entry.status,
                    "timestamp": entry.timestamp,
                },
                sort_keys=True,
            ),
            encoding="utf-8",
        )
    except Exception:
        return


# ============================================================================
# Main hook logic
# ============================================================================

def _handle_pre_tool_use(hook_input: PreToolUseInput, config: Config) -> None:
    command = str(hook_input.tool_input.get("command", ""))
    if not _is_git_push_command(command):
        exit(hook_event_name=HOOK_EVENT_NAME)

    coderabbit_bin = _resolve_coderabbit_binary()
    if coderabbit_bin is None:
        exit(
            text="[coderabbit] CLI not found. Skipping commit review.",
            to_stderr=True,
            hook_event_name=HOOK_EVENT_NAME,
        )
    coderabbit_cmd = coderabbit_bin

    git_cwd = _extract_git_cwd(command, hook_input.cwd)
    repo_root = _get_repo_root(git_cwd)
    if repo_root is None:
        exit(hook_event_name=HOOK_EVENT_NAME)
        return
    repo_root_path = repo_root

    base_commit = _get_upstream_commit(repo_root_path)
    base_branch = None if base_commit else _get_default_base_branch(repo_root_path)
    base_sha = base_commit
    if base_sha is None and base_branch:
        base_sha = _rev_parse(repo_root_path, f"refs/remotes/origin/{base_branch}") or _rev_parse(repo_root_path, base_branch)

    branch = _get_branch(repo_root_path)
    head_sha = _get_head_sha(repo_root_path)

    if base_sha and head_sha and config.review_type == "committed":
        commit_count = _count_commits(repo_root_path, base_sha, head_sha)
        if commit_count == 0:
            exit(hook_event_name=HOOK_EVENT_NAME)

    if config.cache_dir and base_sha and head_sha:
        cache_path = _cache_file(config.cache_dir, repo_root_path)
        cached = _load_cache(cache_path)
        if cached and cached.status == "clean":
            fresh = (time.time() - cached.timestamp) <= config.cache_ttl_sec
            if fresh and cached.review_type == config.review_type and cached.head_sha == head_sha and cached.base_sha == base_sha:
                exit(hook_event_name=HOOK_EVENT_NAME)

    cmd = [
        coderabbit_cmd,
        "--prompt-only",
        "--no-color",
        "--cwd",
        str(repo_root_path),
        "--type",
        config.review_type,
    ]
    if base_sha:
        cmd.extend(["--base-commit", base_sha])
    elif base_branch:
        cmd.extend(["--base", base_branch])

    code, stdout, stderr, timed_out = _run(cmd, cwd=repo_root_path, timeout_sec=config.timeout_sec)
    combined_output = _normalize_output(stdout, stderr)

    if code != 0:
        excerpt = _truncate(combined_output or "(no output)", config.max_chars)
        details = (
            "[coderabbit] CLI failed before push.\n"
            f"Repo: {repo_root_path}\n"
            f"Branch: {branch}\n"
            f"Exit code: {code}{' (timeout)' if timed_out else ''}\n\n"
            f"Output:\n{excerpt}\n"
        )
        if config.on_cli_failure == "allow":
            exit(text=details, to_stderr=True, hook_event_name=HOOK_EVENT_NAME)
        exit(decision="deny", reason=details, hook_event_name=HOOK_EVENT_NAME)

    findings = _parse_findings(combined_output, repo_root_path)
    if not findings:
        if config.cache_dir and base_sha and head_sha:
            _store_cache(
                _cache_file(config.cache_dir, repo_root_path),
                CacheEntry(
                    head_sha=head_sha,
                    base_sha=base_sha,
                    review_type=config.review_type,
                    status="clean",
                    timestamp=time.time(),
                ),
            )
        exit(hook_event_name=HOOK_EVENT_NAME)

    excerpt = _truncate(combined_output, config.max_chars)
    summary = _summarize_findings(findings)
    exit(
        decision="deny",
        reason=(
            "[coderabbit] Findings detected before push.\n"
            f"Repo: {repo_root_path}\n"
            f"Branch: {branch}\n"
            f"Findings: {len(findings)}\n\n"
            f"Summary:\n{summary}\n\n"
            f"Excerpt:\n{excerpt}\n\n"
            "Fix issues, then re-run push to recheck."
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
