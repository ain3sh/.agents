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
from typing import Any

# add hooks dir to path for rel import
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils import (  # type: ignore
    HookInputError,
    SessionEndInput,
    exit,
    get_toml_section,
    load_toml,
    read_input_as,
)

HOOK_EVENT_NAME = "SessionEnd"


@dataclass(slots=True, frozen=True)
class Config:
    tail_count: int
    tail_when: set[str]
    todo_when: set[str]


def _parse_args(argv: list[str]) -> Config:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--config-file", default="", help="Path to TOML config file")
    parser.add_argument("--tail", type=int, default=None, help="Number of user prompts to include in tail")
    parser.add_argument(
        "--tail-when",
        default="",
        help="Comma-separated SessionEnd reasons to store tail",
    )
    parser.add_argument(
        "--todo-when",
        default="",
        help="Comma-separated SessionEnd reasons to store todos",
    )
    args = parser.parse_args(argv)

    try:
        config_data = load_toml(args.config_file)
    except OSError as exc:
        exit(
            1,
            text=f"[session_end] Config file error: {exc}",
            to_stderr=True,
            hook_event_name=HOOK_EVENT_NAME,
        )
    except Exception as exc:
        exit(
            1,
            text=f"[session_end] Config parse error: {exc}",
            to_stderr=True,
            hook_event_name=HOOK_EVENT_NAME,
        )

    config = get_toml_section(config_data, "hooks", "session_end", "store_artifacts")

    tail_count = args.tail if args.tail is not None else config.get("tail", 0)
    tail_when = _parse_reasons(args.tail_when) or _parse_reasons(config.get("tail_when"))
    todo_when = _parse_reasons(args.todo_when) or _parse_reasons(config.get("todo_when"))

    return Config(
        tail_count=int(tail_count),
        tail_when=tail_when or {"prompt_input_exit", "other"},
        todo_when=todo_when or {"prompt_input_exit", "other", "clear"},
    )


def _safe_session_id(session_id: str) -> str:
    if not session_id:
        return "session"
    return session_id.replace(os.sep, "_")


def _split_reasons(value: str) -> set[str]:
    return {item for item in (part.strip() for part in value.split(",")) if item}


def _parse_reasons(value: object) -> set[str]:
    if isinstance(value, list):
        return {item for item in value if isinstance(item, str)}
    if isinstance(value, str):
        return _split_reasons(value)
    return set()


def _storage_dir(cwd: str) -> Path:
    stamp = datetime.now().strftime("%m_%d_%Y")
    return Path(cwd) / ".agents" / stamp


def _as_str_dict(value: object) -> dict[str, object] | None:
    if isinstance(value, dict):
        return {str(key): val for key, val in value.items()}
    return None

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

def _format_tail(messages: list[tuple[str, str]]) -> str:
    lines = ["# Session Tail", ""]
    for role, content in messages:
        lines.append(f"## {role}")
        lines.append(content.strip())
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _scan_transcript_reverse(
    path: Path,
    *,
    tail_count: int,
    capture_tail: bool,
    capture_todos: bool,
) -> tuple[str | None, str | None]:
    if (not capture_tail or tail_count <= 0) and not capture_todos:
        return None, None

    FileReadBackwards: type[Any] | None = None
    try:
        import importlib

        module = importlib.import_module("file_read_backwards")
        FileReadBackwards = getattr(module, "FileReadBackwards", None)
    except Exception:
        return _scan_transcript_forward(
            path,
            tail_count=tail_count,
            capture_tail=capture_tail,
            capture_todos=capture_todos,
        )
    if FileReadBackwards is None:
        return _scan_transcript_forward(
            path,
            tail_count=tail_count,
            capture_tail=capture_tail,
            capture_todos=capture_todos,
        )

    tail_messages_rev: list[tuple[str, str]] = []
    user_count = 0
    tail_done = (not capture_tail) or tail_count <= 0

    latest_todos: str | None = None
    todos_done = not capture_todos

    try:
        with FileReadBackwards(str(path), encoding="utf-8") as handle:
            for raw_line in handle:
                line = raw_line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue

                item = _as_str_dict(data)
                if item is None:
                    continue

                if capture_todos and not todos_done:
                    tool_name = item.get("tool_name") or item.get("name")
                    if tool_name == "TodoWrite":
                        tool_input = _as_str_dict(
                            item.get("tool_input")
                            or item.get("input")
                            or item.get("arguments")
                        )
                        if tool_input is not None:
                            todos = tool_input.get("todos")
                            if isinstance(todos, str):
                                todos = todos.strip()
                                if todos:
                                    latest_todos = f"{todos}\n"
                                    todos_done = True

                if capture_tail and not tail_done:
                    role, content = _extract_role_content(item)
                    if role is not None and content is not None:
                        tail_messages_rev.append((role, content))
                        if role == "user":
                            user_count += 1
                            if user_count >= tail_count:
                                tail_done = True

                if tail_done and todos_done:
                    break
    except OSError:
        return None, None

    tail_content: str | None = None
    if capture_tail and tail_count > 0 and user_count > 0 and tail_messages_rev:
        messages = list(reversed(tail_messages_rev))
        start_index = next((i for i, (role, _) in enumerate(messages) if role == "user"), 0)
        messages = messages[start_index:]
        if messages:
            tail_content = _format_tail(messages)

    return tail_content, (latest_todos if capture_todos else None)


def _scan_transcript_forward(
    path: Path,
    *,
    tail_count: int,
    capture_tail: bool,
    capture_todos: bool,
) -> tuple[str | None, str | None]:
    if (not capture_tail or tail_count <= 0) and not capture_todos:
        return None, None

    tail_buffer: list[tuple[str, str]] = []
    user_positions: list[int] = []
    latest_todos: str | None = None

    try:
        with path.open("r", encoding="utf-8") as handle:
            for raw_line in handle:
                line = raw_line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue

                item = _as_str_dict(data)
                if item is None:
                    continue

                if capture_todos:
                    tool_name = item.get("tool_name") or item.get("name")
                    if tool_name == "TodoWrite":
                        tool_input = _as_str_dict(
                            item.get("tool_input")
                            or item.get("input")
                            or item.get("arguments")
                        )
                        if tool_input is not None:
                            todos = tool_input.get("todos")
                            if isinstance(todos, str):
                                todos = todos.strip()
                                if todos:
                                    latest_todos = f"{todos}\n"

                if capture_tail and tail_count > 0:
                    role, content = _extract_role_content(item)
                    if role is None or content is None:
                        continue

                    tail_buffer.append((role, content))
                    if role == "user":
                        user_positions.append(len(tail_buffer) - 1)
                        if len(user_positions) > tail_count:
                            cut_index = user_positions[1]
                            tail_buffer = tail_buffer[cut_index:]
                            user_positions = [i - cut_index for i in user_positions[1:]]
    except OSError:
        return None, None

    tail_content: str | None = None
    if capture_tail and tail_count > 0 and user_positions:
        start = user_positions[0]
        messages = tail_buffer[start:]
        if messages:
            tail_content = _format_tail(messages)

    return tail_content, (latest_todos if capture_todos else None)


def _scan_transcript(
    path: Path,
    *,
    tail_count: int,
    capture_tail: bool,
    capture_todos: bool,
) -> tuple[str | None, str | None]:
    return _scan_transcript_reverse(
        path,
        tail_count=tail_count,
        capture_tail=capture_tail,
        capture_todos=capture_todos,
    )


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
        exit(
            1,
            text=f"[session_end] Hook input error: {exc}",
            to_stderr=True,
            hook_event_name=HOOK_EVENT_NAME,
        )

    transcript_path = Path(hook_input.transcript_path).expanduser()
    if not transcript_path.exists():
        exit(hook_event_name=HOOK_EVENT_NAME)

    want_tail = hook_input.reason in config.tail_when and config.tail_count > 0
    want_todos = hook_input.reason in config.todo_when

    tail_content, todos = _scan_transcript(
        transcript_path,
        tail_count=config.tail_count,
        capture_tail=want_tail,
        capture_todos=want_todos,
    )

    safe_id = _safe_session_id(hook_input.session_id)
    base_dir = _storage_dir(hook_input.cwd)

    if want_tail and tail_content:
        _write_file(base_dir / f"{safe_id}_tail.md", tail_content)

    if want_todos and todos:
        _write_file(base_dir / f"{safe_id}_todo.md", todos)

    exit(hook_event_name=HOOK_EVENT_NAME)


if __name__ == "__main__":
    raise SystemExit(main())
