#!/usr/bin/env python3
"""SessionEnd hook to store session tail and latest todos."""
from __future__ import annotations
import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

# add hooks dir to path for rel import
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils import HookInputError, SessionEndInput, exit, read_input_as  # type: ignore


@dataclass(slots=True, frozen=True)
class Config:
    tail_count: int
    tail_when: set[str]
    todo_when: set[str]


def _parse_args(argv: list[str]) -> Config:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--tail", type=int, default=0, help="Number of user prompts to include in tail")
    parser.add_argument(
        "--tail-when",
        default="prompt_input_exit,other",
        help="Comma-separated SessionEnd reasons to store tail",
    )
    parser.add_argument(
        "--todo-when",
        default="prompt_input_exit,other,clear",
        help="Comma-separated SessionEnd reasons to store todos",
    )
    args = parser.parse_args(argv)
    return Config(
        tail_count=args.tail,
        tail_when=_split_reasons(args.tail_when),
        todo_when=_split_reasons(args.todo_when),
    )


def _safe_session_id(session_id: str) -> str:
    if not session_id:
        return "session"
    return session_id.replace(os.sep, "_")


def _split_reasons(value: str) -> set[str]:
    return {item for item in (part.strip() for part in value.split(",")) if item}


def _storage_dir(cwd: str) -> Path:
    stamp = datetime.now().strftime("%m_%d_%Y")
    return Path(cwd) / ".agents" / stamp


def _as_str_dict(value: object) -> dict[str, object] | None:
    if isinstance(value, dict):
        return {str(key): val for key, val in value.items()}
    return None


def _read_transcript_lines(path: Path) -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return items
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        data_dict = _as_str_dict(data)
        if data_dict is not None:
            items.append(data_dict)
    return items


def _stringify_content(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
                continue
            item_dict = _as_str_dict(item)
            if item_dict is None:
                continue
            text_value = item_dict.get("text")
            if isinstance(text_value, str):
                parts.append(text_value)
        return "".join(parts)
    if content is None:
        return ""
    return str(content)


def _extract_role_content(item: dict[str, object]) -> tuple[str | None, str | None]:
    role = item.get("role")
    content = item.get("content")
    if isinstance(role, str):
        return role, _stringify_content(content)

    message = _as_str_dict(item.get("message"))
    if message is not None:
        msg_role = message.get("role")
        msg_content = message.get("content")
        if isinstance(msg_role, str):
            return msg_role, _stringify_content(msg_content)

    msg_type = item.get("type")
    if msg_type in {"user_message", "assistant_message", "tool_message"}:
        role_map = {
            "user_message": "user",
            "assistant_message": "assistant",
            "tool_message": "tool",
        }
        role_value = role_map.get(msg_type)
        if role_value is not None:
            content_value = item.get("text") or item.get("content")
            return role_value, _stringify_content(content_value)

    return None, None


def _extract_tail(items: list[dict[str, object]], tail_count: int) -> str | None:
    if tail_count <= 0:
        return None

    messages: list[tuple[str, str]] = []
    user_indices: list[int] = []
    for item in items:
        role, content = _extract_role_content(item)
        if role is not None and content is not None:
            if role == "user":
                user_indices.append(len(messages))
            messages.append((role, content))

    if not user_indices:
        return None

    start_index = user_indices[-tail_count] if len(user_indices) >= tail_count else user_indices[0]
    tail_messages = messages[start_index:]
    if not tail_messages:
        return None

    lines = ["# Session Tail", ""]
    for role, content in tail_messages:
        lines.append(f"## {role}")
        lines.append(content.strip())
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _extract_latest_todos(items: list[dict[str, object]]) -> str | None:
    latest: str | None = None
    for item in items:
        tool_name = item.get("tool_name") or item.get("name")
        if tool_name != "TodoWrite":
            continue

        tool_input = _as_str_dict(item.get("tool_input") or item.get("input") or item.get("arguments"))
        if tool_input is None:
            continue
        todos = tool_input.get("todos")
        if isinstance(todos, str):
            todos = todos.strip()
            if todos:
                latest = f"{todos}\n"

    return latest


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.write_text(content, encoding="utf-8")
    except OSError:
        return


def main():
    config = _parse_args(sys.argv[1:])

    try:
        hook_input = read_input_as(SessionEndInput)
    except HookInputError as exc:
        exit(1, text=f"[session_end] Hook input error: {exc}", to_stderr=True)

    transcript_path = Path(hook_input.transcript_path).expanduser()
    if not transcript_path.exists():
        exit()

    items = _read_transcript_lines(transcript_path)
    if not items:
        exit()

    safe_id = _safe_session_id(hook_input.session_id)
    base_dir = _storage_dir(hook_input.cwd)

    if hook_input.reason in config.tail_when:
        tail_content = _extract_tail(items, config.tail_count)
        if tail_content:
            _write_file(base_dir / f"{safe_id}_tail.md", tail_content)

    if hook_input.reason in config.todo_when:
        todos = _extract_latest_todos(items)
        if todos:
            _write_file(base_dir / f"{safe_id}_todo.md", todos)

    exit()


if __name__ == "__main__":
    raise SystemExit(main())
