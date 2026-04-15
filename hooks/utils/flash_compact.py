"""Shared utilities for flash-compact hooks and scripts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from typing import Callable, Literal

from .tokens import count_tokens

DEFAULT_FLASH_COMPACT_STATE_DIR = "~/.agents/state/flash-compact"
DEFAULT_FLASH_COMPACT_SESSIONS_DIR = "~/.factory/sessions"
DEFAULT_FLASH_COMPACT_MORPH_API_URL = "https://api.morphllm.com/v1/compact"
DEFAULT_FLASH_COMPACT_PROMPT_CACHE_DIRNAME = "prompt-cache"
SYSTEM_REMINDER_PREFIX = "<system-reminder>"
MAX_TOOL_INPUT_CHARS = 500
MAX_TOOL_RESULT_CHARS = 2000
DEFAULT_EXECUTE_INLINE_CHARS = 300
FILE_PATH_LINE_RE = re.compile(r"[/~\w.-]+\.(?:ts|tsx|js|jsx|py|json|md|sh|toml|ya?ml)(?::\d+)?")
HIGH_SIGNAL_LINE_RE = re.compile(
    r"(?i)\b(error|errors|failed|failure|warning|warnings|exception|traceback|assert|cannot\b|enoent|syntaxerror|typeerror|referenceerror|request cancelled|waiting for authentication)\b"
)


@dataclass(slots=True, frozen=True)
class TranscriptSnapshot:
    messages: list[dict[str, str]]
    transcript: str
    token_count: int
    user_turn_count: int
    latest_user_prompt: str


@dataclass(slots=True, frozen=True)
class FlashCompactDefaults:
    state_dir: Path
    prompt_cache_dir: Path
    sessions_dir: Path
    morph_api_url: str


@dataclass(slots=True, frozen=True)
class CompactEntry:
    kind: Literal["user_text", "assistant_text", "tool_call", "tool_result", "todo_state", "ignored"]
    role: str
    message_index: int
    turn_index: int
    tool_name: str = ""
    content: str = ""
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class ReduceContext:
    is_recent: bool
    query: str
    config: "CompactViewConfig"


@dataclass(slots=True, frozen=True)
class CompactViewConfig:
    use_typed_reducers: bool = True
    recent_turns_raw: int = 4
    execute_short_output_chars: int = 3000
    execute_head_lines: int = 20
    execute_tail_lines: int = 30
    execute_max_signal_lines: int = 80
    read_large_output_chars: int = 4000
    todo_keep_latest_old: bool = True


@dataclass(slots=True)
class SessionBudgetState:
    session_id: str
    transcript_path: str
    cwd: str
    last_seen_user_turn_count: int = 0
    last_compact_user_turn_count: int = 0
    last_advisory_user_turn_count: int = 0
    last_estimated_tokens: int = 0
    last_compact_tokens: int = 0
    pending_query: str = ""
    cooldown_until_user_turn_count: int = 0
    blocked_prompt_path: str = ""
    updated_at: str = ""

    @classmethod
    def from_dict(
        cls,
        data: dict[str, object],
        *,
        session_id: str,
        transcript_path: str,
        cwd: str,
    ) -> "SessionBudgetState":
        return cls(
            session_id=str(data.get("session_id") or session_id),
            transcript_path=str(data.get("transcript_path") or transcript_path),
            cwd=str(data.get("cwd") or cwd),
            last_seen_user_turn_count=int(data.get("last_seen_user_turn_count") or 0),
            last_compact_user_turn_count=int(data.get("last_compact_user_turn_count") or 0),
            last_advisory_user_turn_count=int(data.get("last_advisory_user_turn_count") or 0),
            last_estimated_tokens=int(data.get("last_estimated_tokens") or 0),
            last_compact_tokens=int(data.get("last_compact_tokens") or 0),
            pending_query=str(data.get("pending_query") or ""),
            cooldown_until_user_turn_count=int(data.get("cooldown_until_user_turn_count") or 0),
            blocked_prompt_path=str(data.get("blocked_prompt_path") or ""),
            updated_at=str(data.get("updated_at") or ""),
        )

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True, frozen=True)
class CheckpointMetadata:
    session_id: str
    created_at: str
    cwd: str
    project_hash: str
    query: str
    input_tokens: int
    output_tokens: int
    compression_ratio: float
    compact_output_path: str
    metadata_path: str
    blocked_prompt_path: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "CheckpointMetadata":
        return cls(
            session_id=str(data.get("session_id") or ""),
            created_at=str(data.get("created_at") or ""),
            cwd=str(data.get("cwd") or ""),
            project_hash=str(data.get("project_hash") or ""),
            query=str(data.get("query") or ""),
            input_tokens=int(data.get("input_tokens") or 0),
            output_tokens=int(data.get("output_tokens") or 0),
            compression_ratio=float(data.get("compression_ratio") or 0.0),
            compact_output_path=str(data.get("compact_output_path") or ""),
            metadata_path=str(data.get("metadata_path") or ""),
            blocked_prompt_path=str(data.get("blocked_prompt_path") or ""),
        )

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


Reducer = Callable[[CompactEntry, ReduceContext], list[str]]


def _flash_compact_default(
    config_data: dict[str, object] | None,
    key: str,
) -> str:
    if not isinstance(config_data, dict):
        return ""
    flash_compact = config_data.get("flash_compact")
    if not isinstance(flash_compact, dict):
        return ""
    defaults = flash_compact.get("defaults")
    if not isinstance(defaults, dict):
        return ""
    value = defaults.get(key)
    return str(value).strip() if value is not None else ""


def load_flash_compact_defaults(
    config_data: dict[str, object] | None = None,
) -> FlashCompactDefaults:
    state_dir_value = (
        os.environ.get("FLASH_COMPACT_STATE_DIR")
        or _flash_compact_default(config_data, "state_dir")
        or DEFAULT_FLASH_COMPACT_STATE_DIR
    )
    state_dir = Path(state_dir_value).expanduser()
    prompt_cache_dir_value = (
        os.environ.get("FLASH_COMPACT_PROMPT_CACHE_DIR")
        or _flash_compact_default(config_data, "prompt_cache_dir")
        or str(state_dir / DEFAULT_FLASH_COMPACT_PROMPT_CACHE_DIRNAME)
    )
    sessions_dir_value = (
        os.environ.get("FLASH_COMPACT_SESSIONS_DIR")
        or _flash_compact_default(config_data, "sessions_dir")
        or DEFAULT_FLASH_COMPACT_SESSIONS_DIR
    )
    morph_api_url = (
        os.environ.get("MORPH_API_URL")
        or _flash_compact_default(config_data, "morph_api_url")
        or DEFAULT_FLASH_COMPACT_MORPH_API_URL
    )
    return FlashCompactDefaults(
        state_dir=state_dir,
        prompt_cache_dir=Path(prompt_cache_dir_value).expanduser(),
        sessions_dir=Path(sessions_dir_value).expanduser(),
        morph_api_url=morph_api_url,
    )


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def safe_session_id(session_id: str) -> str:
    if not session_id:
        return "session"
    return session_id.replace(os.sep, "_")


def project_hash(cwd: str) -> str:
    resolved = str(Path(cwd).expanduser().resolve()) if cwd else ""
    return hashlib.sha1(resolved.encode("utf-8")).hexdigest()[:16]


def read_json(path: Path) -> dict[str, object] | None:
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as handle:
            value = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def write_json(path: Path, data: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)
        handle.write("\n")


def get_morph_api_key() -> str:
    key = os.environ.get("MORPH_API_KEY")
    if key:
        return key

    mcp_path = Path.home() / ".factory" / "mcp.json"
    mcp = read_json(mcp_path) if mcp_path.exists() else None
    if mcp is None:
        raise RuntimeError("MORPH_API_KEY not found in environment or ~/.factory/mcp.json")

    codebase = mcp.get("mcpServers", {})
    if not isinstance(codebase, dict):
        raise RuntimeError("Invalid ~/.factory/mcp.json structure")
    server = codebase.get("codebase", {})
    if not isinstance(server, dict):
        raise RuntimeError("Invalid codebase MCP configuration")
    env = server.get("env", {})
    if not isinstance(env, dict):
        raise RuntimeError("Invalid codebase MCP environment configuration")
    key = env.get("MORPH_API_KEY")
    if isinstance(key, str) and key:
        return key

    raise RuntimeError("MORPH_API_KEY not found in environment or ~/.factory/mcp.json")


def truncate_text(text: str, max_chars: int) -> str:
    if max_chars <= 0 or len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "\n... (truncated)"


def truncate_inline_text(text: str, max_chars: int = DEFAULT_EXECUTE_INLINE_CHARS) -> str:
    return truncate_text(text.replace("\n", " "), max_chars)


def _normalize_text_block(text: str) -> str:
    stripped = text.strip()
    if not stripped or stripped.startswith(SYSTEM_REMINDER_PREFIX):
        return ""
    return stripped


def _stringify_tool_result(content: object) -> str:
    if isinstance(content, str):
        return content.strip()
    if not isinstance(content, list):
        return ""

    parts: list[str] = []
    for item in content:
        if not isinstance(item, dict):
            continue
        text = str(item.get("text") or item.get("content") or "").strip()
        if text:
            parts.append(text)
    return "\n".join(parts).strip()


def _tool_input_summary(tool_name: str, tool_input: dict[str, object]) -> str:
    if tool_name == "Execute":
        command = tool_input.get("command")
        return truncate_inline_text(str(command or ""))
    if tool_name == "Read":
        file_path = tool_input.get("file_path")
        return truncate_inline_text(str(file_path or ""))
    encoded = json.dumps(tool_input, separators=(",", ":"), ensure_ascii=False)
    return truncate_inline_text(encoded, MAX_TOOL_INPUT_CHARS)


def _signal_line(line: str) -> bool:
    return bool(HIGH_SIGNAL_LINE_RE.search(line) or FILE_PATH_LINE_RE.search(line))


def _split_non_empty_lines(text: str) -> list[str]:
    return [line.rstrip() for line in text.splitlines() if line.strip()]


def _render_indented_block(title: str, lines: list[str]) -> list[str]:
    if not lines:
        return []
    return [f"{title}:"] + [f"  {truncate_inline_text(line, 500)}" for line in lines]


def _render_tool_call_fallback(entry: CompactEntry) -> list[str]:
    if entry.tool_name:
        summary = _tool_input_summary(entry.tool_name, entry.metadata.get("tool_input", {}) if isinstance(entry.metadata.get("tool_input"), dict) else {})
        return [f"[tool_call: {entry.tool_name}]", f"input: {summary}"] if summary else [f"[tool_call: {entry.tool_name}]"]
    if entry.content:
        return [f"[tool_call: {truncate_inline_text(entry.content, MAX_TOOL_INPUT_CHARS)}]"]
    return []


def _render_tool_result_fallback(entry: CompactEntry) -> list[str]:
    label = entry.tool_name or "tool"
    text = truncate_text(entry.content, MAX_TOOL_RESULT_CHARS)
    lines = [f"[tool_result: {label}]"]
    lines.extend(text.splitlines())
    return lines


def extract_conversation(path: Path) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = []
    for message in build_compact_messages(
        extract_compact_entries(path),
        query="",
        preserve_recent=0,
        config=CompactViewConfig(use_typed_reducers=False, recent_turns_raw=0, todo_keep_latest_old=False),
    ):
        messages.append(message)
    return messages


def extract_compact_entries(path: Path) -> list[CompactEntry]:
    if not path.exists():
        return []

    entries: list[CompactEntry] = []
    tool_registry: dict[str, dict[str, object]] = {}
    current_turn = 0
    message_index = 0

    try:
        with path.open("r", encoding="utf-8") as handle:
            for raw_line in handle:
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    item = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(item, dict) or item.get("type") != "message":
                    continue
                message = item.get("message")
                if not isinstance(message, dict):
                    continue
                role = message.get("role")
                if not isinstance(role, str) or not role:
                    continue

                message_index += 1
                if role == "user":
                    current_turn += 1
                turn_index = current_turn
                content = message.get("content", [])

                if isinstance(content, str):
                    text = _normalize_text_block(content)
                    if text:
                        entries.append(
                            CompactEntry(
                                kind="user_text" if role == "user" else "assistant_text",
                                role=role,
                                message_index=message_index,
                                turn_index=turn_index,
                                content=text,
                            )
                        )
                    continue

                if not isinstance(content, list):
                    continue

                for block in content:
                    if not isinstance(block, dict):
                        continue
                    block_type = str(block.get("type") or "")
                    if block_type == "text":
                        text = _normalize_text_block(str(block.get("text") or ""))
                        if text:
                            entries.append(
                                CompactEntry(
                                    kind="user_text" if role == "user" else "assistant_text",
                                    role=role,
                                    message_index=message_index,
                                    turn_index=turn_index,
                                    content=text,
                                )
                            )
                        continue

                    if block_type == "thinking":
                        continue

                    if block_type == "tool_use":
                        tool_name = str(block.get("name") or "")
                        tool_input = block.get("input", {})
                        if not isinstance(tool_input, dict):
                            tool_input = {}
                        tool_use_id = str(block.get("id") or "")
                        if tool_use_id:
                            tool_registry[tool_use_id] = {
                                "tool_name": tool_name,
                                "tool_input": tool_input,
                            }

                        if tool_name == "TodoWrite":
                            todos = tool_input.get("todos")
                            if isinstance(todos, str) and todos.strip():
                                entries.append(
                                    CompactEntry(
                                        kind="todo_state",
                                        role=role,
                                        message_index=message_index,
                                        turn_index=turn_index,
                                        tool_name=tool_name,
                                        content=todos.strip(),
                                        metadata={"tool_input": tool_input},
                                    )
                                )
                            continue

                        entries.append(
                            CompactEntry(
                                kind="tool_call",
                                role=role,
                                message_index=message_index,
                                turn_index=turn_index,
                                tool_name=tool_name,
                                content=_tool_input_summary(tool_name, tool_input),
                                metadata={"tool_input": tool_input, "tool_use_id": tool_use_id},
                            )
                        )
                        continue

                    if block_type == "tool_result":
                        tool_use_id = str(block.get("tool_use_id") or "")
                        registry = tool_registry.get(tool_use_id, {})
                        tool_name = str(registry.get("tool_name") or "")
                        tool_input = registry.get("tool_input", {})
                        if tool_name == "TodoWrite":
                            continue
                        text = _stringify_tool_result(block.get("content", ""))
                        if text:
                            entries.append(
                                CompactEntry(
                                    kind="tool_result",
                                    role=role,
                                    message_index=message_index,
                                    turn_index=turn_index,
                                    tool_name=tool_name,
                                    content=text,
                                    metadata={
                                        "tool_use_id": tool_use_id,
                                        "tool_input": tool_input if isinstance(tool_input, dict) else {},
                                        "is_error": bool(block.get("is_error", False)),
                                    },
                                )
                            )
    except OSError:
        return []

    return entries


def build_transcript(messages: list[dict[str, str]]) -> str:
    lines: list[str] = []
    for message in messages:
        lines.append(f"--- {message['role'].upper()} ---")
        lines.extend(message["content"].splitlines() or [""])
        lines.append("")
    return "\n".join(lines).rstrip()


def snapshot_transcript(path: Path) -> TranscriptSnapshot:
    messages = extract_conversation(path)
    transcript = build_transcript(messages)
    latest_user_prompt = ""
    user_turn_count = 0
    for message in messages:
        if message["role"] == "user":
            user_turn_count += 1
            latest_user_prompt = message["content"]
    return TranscriptSnapshot(
        messages=messages,
        transcript=transcript,
        token_count=count_tokens(transcript) if transcript else 0,
        user_turn_count=user_turn_count,
        latest_user_prompt=latest_user_prompt,
    )


def _default_reduce(entry: CompactEntry, context: ReduceContext) -> list[str]:
    if entry.kind in {"user_text", "assistant_text"}:
        return entry.content.splitlines()
    if entry.kind == "todo_state":
        return ["[todo_state]"] + entry.content.splitlines()
    if entry.kind == "tool_call":
        return _render_tool_call_fallback(entry)
    if entry.kind == "tool_result":
        return _render_tool_result_fallback(entry)
    return []


def _reduce_execute_tool_call(entry: CompactEntry, context: ReduceContext) -> list[str]:
    if not context.is_recent:
        return []
    return _render_tool_call_fallback(entry)


def _reduce_execute_result(entry: CompactEntry, context: ReduceContext) -> list[str]:
    if context.is_recent or len(entry.content) <= context.config.execute_short_output_chars:
        return _render_tool_result_fallback(entry)

    tool_input = entry.metadata.get("tool_input", {})
    command = ""
    risk_level = ""
    timeout = ""
    if isinstance(tool_input, dict):
        command = str(tool_input.get("command") or "")
        risk_level = str(tool_input.get("riskLevel") or "")
        timeout_value = tool_input.get("timeout")
        timeout = str(timeout_value) if timeout_value not in (None, "") else ""

    raw_lines = _split_non_empty_lines(entry.content)
    head = raw_lines[: context.config.execute_head_lines]
    tail = raw_lines[-context.config.execute_tail_lines :] if len(raw_lines) > context.config.execute_head_lines else []
    protected = set(head) | set(tail)
    signal_lines: list[str] = []
    seen = set(protected)
    for line in raw_lines:
        if line in seen:
            continue
        if not _signal_line(line):
            continue
        signal_lines.append(line)
        seen.add(line)
        if len(signal_lines) >= context.config.execute_max_signal_lines:
            break

    is_error = entry.metadata.get("is_error") is True
    lines = ["[tool_result: Execute summary]"]
    if command:
        lines.append(f"command: {truncate_inline_text(command)}")
    if risk_level:
        lines.append(f"risk_level: {risk_level}")
    if timeout:
        lines.append(f"timeout: {timeout}")
    if is_error:
        lines.append("is_error: true")

    if not is_error and not signal_lines:
        lines.append("output: omitted (non-error low-signal command output)")
        return lines

    lines.extend(_render_indented_block("first_lines", head))
    lines.extend(_render_indented_block("high_signal", signal_lines))
    lines.extend(_render_indented_block("last_lines", tail))
    return lines


def _reduce_read_tool_call(entry: CompactEntry, context: ReduceContext) -> list[str]:
    if not context.is_recent:
        return []
    return _render_tool_call_fallback(entry)


def _reduce_read_result(entry: CompactEntry, context: ReduceContext) -> list[str]:
    if context.is_recent or len(entry.content) <= context.config.read_large_output_chars:
        return _render_tool_result_fallback(entry)

    tool_input = entry.metadata.get("tool_input", {})
    file_path = ""
    offset = ""
    limit = ""
    if isinstance(tool_input, dict):
        file_path = str(tool_input.get("file_path") or "")
        offset_value = tool_input.get("offset")
        limit_value = tool_input.get("limit")
        offset = str(offset_value) if offset_value not in (None, "") else ""
        limit = str(limit_value) if limit_value not in (None, "") else ""

    lines = ["[tool_result: Read summary]"]
    if file_path:
        lines.append(f"path: {file_path}")
    if offset:
        lines.append(f"offset: {offset}")
    if limit:
        lines.append(f"limit: {limit}")
    lines.append("large_output: omitted")
    return lines


def _reduce_todo_state(entry: CompactEntry, context: ReduceContext) -> list[str]:
    return ["[todo_state]"] + entry.content.splitlines()


def _reduce_entry(entry: CompactEntry, context: ReduceContext) -> list[str]:
    if not context.config.use_typed_reducers:
        return _default_reduce(entry, context)

    if entry.kind == "tool_call" and entry.tool_name == "Execute":
        return _reduce_execute_tool_call(entry, context)
    if entry.kind == "tool_result" and entry.tool_name == "Execute":
        return _reduce_execute_result(entry, context)
    if entry.kind == "tool_call" and entry.tool_name == "Read":
        return _reduce_read_tool_call(entry, context)
    if entry.kind == "tool_result" and entry.tool_name == "Read":
        return _reduce_read_result(entry, context)
    if entry.kind == "todo_state":
        return _reduce_todo_state(entry, context)
    return _default_reduce(entry, context)


def build_compact_messages(
    entries: list[CompactEntry],
    *,
    query: str,
    preserve_recent: int,
    config: CompactViewConfig,
) -> list[dict[str, str]]:
    if not entries:
        return []

    max_turn_index = max((entry.turn_index for entry in entries), default=0)
    recent_turns = max(config.recent_turns_raw, preserve_recent)
    recent_cutoff = max_turn_index + 1
    if recent_turns > 0 and max_turn_index > 0:
        recent_cutoff = max(1, max_turn_index - recent_turns + 1)

    latest_old_todo_message_index: int | None = None
    if config.todo_keep_latest_old:
        for entry in entries:
            if entry.kind == "todo_state" and entry.turn_index < recent_cutoff:
                latest_old_todo_message_index = entry.message_index

    messages: list[dict[str, str]] = []
    current_message_index: int | None = None
    current_role = ""
    current_lines: list[str] = []

    def flush() -> None:
        nonlocal current_lines, current_role
        if current_role and current_lines:
            messages.append({"role": current_role, "content": "\n".join(current_lines).strip()})
        current_lines = []

    for entry in entries:
        if current_message_index != entry.message_index:
            flush()
            current_message_index = entry.message_index
            current_role = entry.role

        if (
            entry.kind == "todo_state"
            and not (entry.turn_index >= recent_cutoff)
            and latest_old_todo_message_index is not None
            and entry.message_index != latest_old_todo_message_index
        ):
            continue

        context = ReduceContext(
            is_recent=entry.turn_index >= recent_cutoff,
            query=query,
            config=config,
        )
        current_lines.extend(_reduce_entry(entry, context))

    flush()
    return [message for message in messages if message["content"]]


def build_compact_messages_from_path(
    path: Path,
    *,
    query: str,
    preserve_recent: int,
    config: CompactViewConfig,
) -> list[dict[str, str]]:
    return build_compact_messages(
        extract_compact_entries(path),
        query=query,
        preserve_recent=preserve_recent,
        config=config,
    )


def read_session_title(path: Path) -> str:
    try:
        with path.open("r", encoding="utf-8") as handle:
            first = json.loads(handle.readline())
    except (OSError, json.JSONDecodeError):
        return "Untitled"
    if not isinstance(first, dict):
        return "Untitled"
    title = first.get("sessionTitle", first.get("title", "Untitled"))
    return str(title)[:80]


def find_project_sessions(
    project_pattern: str,
    limit: int,
    *,
    sessions_dir: Path | None = None,
) -> list[Path]:
    matches: list[Path] = []
    root = sessions_dir or load_flash_compact_defaults().sessions_dir
    if not root.exists():
        return matches
    for item in root.iterdir():
        if item.is_dir() and project_pattern.lower() in item.name.lower():
            matches.extend(
                sorted(item.glob("*.jsonl"), key=lambda path: path.stat().st_mtime, reverse=True)
            )
    matches.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    return matches[:limit]


def tail_messages_within_token_budget(
    messages: list[dict[str, str]],
    max_tokens: int,
    preserve_recent: int,
) -> list[dict[str, str]]:
    if max_tokens <= 0 or not messages:
        return list(messages)

    selected_rev: list[dict[str, str]] = []
    total_tokens = 0
    minimum_keep = max(0, preserve_recent)

    for message in reversed(messages):
        rendered = f"--- {message['role'].upper()} ---\n{message['content']}\n"
        message_tokens = count_tokens(rendered)
        if len(selected_rev) < minimum_keep or total_tokens + message_tokens <= max_tokens:
            selected_rev.append(message)
            total_tokens += message_tokens
            continue
        break

    return list(reversed(selected_rev))


def morph_compact_messages(
    *,
    messages: list[dict[str, str]],
    query: str,
    compression_ratio: float,
    preserve_recent: int,
    include_markers: bool,
    api_url: str | None = None,
    timeout_seconds: int = 120,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "messages": messages,
        "compression_ratio": compression_ratio,
        "preserve_recent": preserve_recent,
        "include_markers": include_markers,
        "include_line_ranges": False,
    }
    if query:
        payload["query"] = query

    result = subprocess.run(
        [
            "curl",
            "--max-time",
            str(timeout_seconds),
            "--connect-timeout",
            str(min(timeout_seconds, 10)),
            "-sS",
            "-X",
            "POST",
            api_url or load_flash_compact_defaults().morph_api_url,
            "-H",
            "Content-Type: application/json",
            "-H",
            f"Authorization: Bearer {get_morph_api_key()}",
            "--data-binary",
            "@-",
        ],
        capture_output=True,
        text=True,
        input=json.dumps(payload),
        check=False,
    )
    try:
        payload_result = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        if result.returncode != 0:
            raise RuntimeError(f"Morph API request failed: {result.stderr.strip()}") from exc
        raise RuntimeError(f"Morph API returned an invalid response: {result.stdout[:500]}") from exc

    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Morph API request failed")
    if not isinstance(payload_result, dict):
        raise RuntimeError("Morph API returned an invalid response")
    if "error" in payload_result:
        raise RuntimeError(f"Morph API returned an error: {payload_result['error']}")
    return payload_result


def determine_query(
    *,
    custom_instructions: str,
    pending_query: str,
    latest_user_prompt: str,
) -> str:
    for candidate in (custom_instructions, pending_query, latest_user_prompt):
        stripped = candidate.strip()
        if stripped:
            return stripped
    return "current task"


def state_root(
    path_value: str | Path | None = None,
    *,
    config_data: dict[str, object] | None = None,
) -> Path:
    if path_value:
        return Path(path_value).expanduser()
    return load_flash_compact_defaults(config_data).state_dir


def session_state_path(root: Path, session_id: str) -> Path:
    return root / "sessions" / f"{safe_session_id(session_id)}.json"


def latest_checkpoint_path(root: Path, cwd: str) -> Path:
    return root / "latest-by-project" / f"{project_hash(cwd)}.json"


def load_session_budget_state(
    *,
    root: Path,
    session_id: str,
    transcript_path: str,
    cwd: str,
) -> SessionBudgetState:
    path = session_state_path(root, session_id)
    data = read_json(path)
    if data is None:
        return SessionBudgetState(session_id=session_id, transcript_path=transcript_path, cwd=cwd)
    return SessionBudgetState.from_dict(
        data,
        session_id=session_id,
        transcript_path=transcript_path,
        cwd=cwd,
    )


def save_session_budget_state(root: Path, state: SessionBudgetState) -> None:
    state.updated_at = now_utc_iso()
    write_json(session_state_path(root, state.session_id), state.to_dict())


def store_prompt_cache(cache_dir: Path, prompt: str, session_id: str) -> Path:
    cache_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    digest = hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:10]
    path = cache_dir / f"{timestamp}-{safe_session_id(session_id)[:8]}-{digest}.md"
    path.write_text(prompt, encoding="utf-8")

    latest_path = cache_dir / "latest.md"
    try:
        latest_path.unlink(missing_ok=True)
        latest_path.symlink_to(path.name)
    except OSError:
        latest_path.write_text(prompt, encoding="utf-8")
    return path


def record_checkpoint(
    *,
    root: Path,
    state: SessionBudgetState,
    query: str,
    compact_output: str,
    usage: dict[str, object],
) -> CheckpointMetadata:
    created_at = now_utc_iso()
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe_id = safe_session_id(state.session_id)

    checkpoints_dir = root / "checkpoints"
    output_path = checkpoints_dir / f"{safe_id}-{timestamp}.txt"
    metadata_path = checkpoints_dir / f"{safe_id}-{timestamp}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(compact_output, encoding="utf-8")

    metadata = CheckpointMetadata(
        session_id=state.session_id,
        created_at=created_at,
        cwd=state.cwd,
        project_hash=project_hash(state.cwd),
        query=query,
        input_tokens=int(usage.get("input_tokens") or 0),
        output_tokens=int(usage.get("output_tokens") or 0),
        compression_ratio=float(usage.get("compression_ratio") or 0.0),
        compact_output_path=str(output_path),
        metadata_path=str(metadata_path),
        blocked_prompt_path=state.blocked_prompt_path,
    )
    write_json(metadata_path, metadata.to_dict())
    write_json(latest_checkpoint_path(root, state.cwd), metadata.to_dict())
    return metadata


def load_latest_checkpoint(root: Path, cwd: str) -> CheckpointMetadata | None:
    data = read_json(latest_checkpoint_path(root, cwd))
    if data is None:
        return None
    return CheckpointMetadata.from_dict(data)


def read_checkpoint_output(metadata: CheckpointMetadata) -> str:
    path = Path(metadata.compact_output_path).expanduser()
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""
