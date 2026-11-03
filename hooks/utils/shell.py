"""Shell-command tokenizing shared by the Execute guards.

Guards accept a tiny grammar and fail open on anything they cannot classify;
these helpers only split a command into tokens and segments, never interpret it.
"""

from __future__ import annotations

import re
import shlex

SHELL_PUNCTUATION = "|&;<>\n"
ASSIGNMENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*=.*")


def tokenize(command: str) -> list[str]:
    lexer = shlex.shlex(command, posix=False, punctuation_chars=SHELL_PUNCTUATION)
    lexer.commenters = ""
    lexer.whitespace = " \t\r"
    lexer.whitespace_split = True
    return list(lexer)


def normalize_token(token: str) -> str:
    try:
        values = shlex.split(token, posix=True)
    except ValueError:
        return token
    return values[0] if len(values) == 1 else token


def normalize_tokens(tokens: list[str]) -> list[str]:
    return [normalize_token(token) for token in tokens]


def is_shell_operator(token: str) -> bool:
    return (
        token == "\n"
        or bool(token)
        and all(char in SHELL_PUNCTUATION for char in token)
    )


def _is_segment_separator(token: str) -> bool:
    return is_shell_operator(token) and (
        "\n" in token or ";" in token or "&&" in token or "||" in token
    )


def segments(tokens: list[str]) -> list[list[str]]:
    result: list[list[str]] = []
    current: list[str] = []
    for token in tokens:
        if _is_segment_separator(token):
            if current:
                result.append(current)
                current = []
            continue
        current.append(token)
    if current:
        result.append(current)
    return result


def _heredoc_delimiters(line: str) -> list[tuple[str, bool]]:
    """(delimiter, strips_tabs) for each heredoc the line opens, in order."""
    try:
        tokens = tokenize(line)
    except ValueError:
        return []
    return [
        (normalize_token(word.removeprefix("-")), word.startswith("-"))
        for operator, word in zip(tokens, tokens[1:])
        if operator == "<<"
    ]


def strip_heredocs(command: str) -> str:
    """Drop heredoc bodies: they are stdin data, never commands to check."""
    kept: list[str] = []
    pending: list[tuple[str, bool]] = []
    for line in command.split("\n"):
        if pending:
            delimiter, strips_tabs = pending[0]
            if (line.lstrip("\t") if strips_tabs else line) == delimiter:
                pending.pop(0)
            continue
        kept.append(line)
        pending = _heredoc_delimiters(line)
    return "\n".join(kept)
