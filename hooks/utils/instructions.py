"""Shared helpers for instruction-style hooks."""
from __future__ import annotations

import fnmatch
import json
import re
from dataclasses import asdict
from pathlib import Path
from typing import cast

from .types import BaseHookInput, PostToolUseInput

_PLACEHOLDER_RE = re.compile(r"\$\{([^}]+)\}")


def parse_str_list(value: object) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,) if value else ()
    if isinstance(value, list):
        return tuple(item for item in value if isinstance(item, str) and item)
    return ()


def dedupe(items: list[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return tuple(ordered)


def read_text(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        content = path.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return content or None


def try_parse_json(value: object) -> object:
    if not isinstance(value, str):
        return value
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def build_template_context(hook_input: BaseHookInput) -> dict[str, object]:
    context = asdict(hook_input)
    if isinstance(hook_input, PostToolUseInput):
        raw_response = hook_input.tool_response
        parsed = try_parse_json(raw_response)
        context["tool_response"] = parsed
        if parsed is not raw_response:
            context["tool_response_raw"] = raw_response
    return context


def match_when(when: set[str], value: str) -> bool:
    if not when:
        return True
    if "*" in when:
        return True
    return value in when


def match_tool(tool_name: str, pattern: str) -> bool:
    if not pattern or pattern == "*":
        return True
    if pattern.startswith("re:"):
        try:
            return re.search(pattern[3:], tool_name) is not None
        except re.error:
            return False
    return fnmatch.fnmatch(tool_name, pattern)


def _resolve_path(data: object, path: list[str]) -> tuple[bool, object | None]:
    current: object = data
    for part in path:
        if not isinstance(current, dict):
            return False, None
        current_dict = cast(dict[str, object], current)
        if part not in current_dict:
            return False, None
        current = current_dict[part]
    return True, current


def _match_dict(pattern: dict[str, object], value: dict[str, object]) -> bool:
    for key, expected in pattern.items():
        if key not in value:
            return False
        actual = value[key]
        if isinstance(expected, dict):
            if not isinstance(actual, dict):
                return False
            if not _match_dict(cast(dict[str, object], expected), cast(dict[str, object], actual)):
                return False
            continue
        if actual != expected:
            return False
    return True


def match_value(pattern: object | None, value: object) -> bool:
    if pattern is None:
        return True
    if isinstance(pattern, dict):
        pattern_dict = cast(dict[str, object], pattern)
        candidate = value
        if isinstance(candidate, str):
            try:
                candidate = json.loads(candidate)
            except json.JSONDecodeError:
                return False
        if not isinstance(candidate, dict):
            return False
        return _match_dict(pattern_dict, cast(dict[str, object], candidate))
    if not isinstance(pattern, str):
        return False
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, sort_keys=True)
    if pattern.startswith("re:"):
        try:
            return re.search(pattern[3:], text) is not None
        except re.error:
            return False
    return pattern in text


def _stringify_value(value: object) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False)


def _resolve_placeholder(key: str, context: dict[str, object]) -> tuple[bool, str | None, bool]:
    path = [part for part in key.split(".") if part]
    if not path:
        return False, None, False

    if len(path) > 1:
        found, value = _resolve_path(context, path)
        return found, _stringify_value(value) if found else None, False

    candidates: list[str] = []
    value: object | None = None
    if key in context:
        candidates.append("root")
        value = context[key]

    tool_response = context.get("tool_response")
    if isinstance(tool_response, dict) and key in tool_response:
        candidates.append("tool_response")
        value = cast(dict[str, object], tool_response)[key]

    tool_input = context.get("tool_input")
    if isinstance(tool_input, dict) and key in tool_input:
        candidates.append("tool_input")
        if value is None:
            value = cast(dict[str, object], tool_input)[key]

    if not candidates:
        return False, None, False

    ambiguous = len(candidates) > 1
    return True, _stringify_value(value), ambiguous


def interpolate(text: str, context: dict[str, object]) -> tuple[str, set[str], set[str]]:
    missing: set[str] = set()
    ambiguous: set[str] = set()

    def _replace(match: re.Match[str]) -> str:
        key = match.group(1).strip()
        found, value, amb = _resolve_placeholder(key, context)
        if not found:
            missing.add(key)
            return match.group(0)
        if amb:
            ambiguous.add(key)
        return value or ""

    rendered = _PLACEHOLDER_RE.sub(_replace, text)
    return rendered, missing, ambiguous


def render_instructions(
    prompts_dir: Path,
    include_files: tuple[str, ...],
    include_text: tuple[str, ...],
    context: dict[str, object],
) -> tuple[str | None, set[str], set[str]]:
    contents: list[str] = []
    missing_all: set[str] = set()
    ambiguous_all: set[str] = set()

    for filename in include_files:
        text = read_text(prompts_dir / filename)
        if not text:
            continue
        rendered, missing, ambiguous = interpolate(text, context)
        contents.append(rendered)
        missing_all.update(missing)
        ambiguous_all.update(ambiguous)

    for text in include_text:
        rendered, missing, ambiguous = interpolate(text, context)
        contents.append(rendered)
        missing_all.update(missing)
        ambiguous_all.update(ambiguous)

    if not contents:
        return None, missing_all, ambiguous_all
    return "\n\n".join(contents), missing_all, ambiguous_all
