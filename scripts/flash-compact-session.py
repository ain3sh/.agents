#!/usr/bin/env python3
"""Generate a flash-compact checkpoint preview for a Droid session."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "hooks"))
from utils import load_toml  # type: ignore
from utils.flash_compact import (  # type: ignore
    CompactViewConfig,
    build_compact_messages_from_path,
    find_project_sessions,
    load_flash_compact_defaults,
    morph_compact_messages,
    read_session_title,
)


def resolve_session(spec: str, sessions_dir: Path) -> Path:
    """Resolve a session UUID, prefix, or path to a .jsonl file."""
    p = Path(spec)
    if p.exists() and p.suffix == ".jsonl":
        return p

    candidates = []
    for jsonl in sessions_dir.rglob("*.jsonl"):
        if jsonl.stem == spec or jsonl.stem.startswith(spec):
            candidates.append(jsonl)

    if len(candidates) == 1:
        return candidates[0]
    if len(candidates) > 1:
        print(f"Ambiguous prefix '{spec}', matches:", file=sys.stderr)
        for c in sorted(candidates, key=lambda x: x.stat().st_mtime, reverse=True)[:10]:
            title = read_session_title(c)
            print(f"  {c.stem}  {title}", file=sys.stderr)
        sys.exit(1)

    print(f"Error: no session matching '{spec}'", file=sys.stderr)
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Generate a flash-compact view of Droid session history via Morph API")
    parser.add_argument("session", nargs="?", help="Session UUID, prefix, or .jsonl path")
    parser.add_argument(
        "--config-file",
        default=str(Path(__file__).resolve().parents[1] / "configs" / "droid.toml"),
        help="Path to droid.toml for shared flash-compact defaults",
    )
    parser.add_argument("--query", "-q", help="Focus query for relevance-based pruning")
    parser.add_argument("--ratio", "-r", type=float, default=0.5, help="Fraction to keep (default: 0.5)")
    parser.add_argument("--recent", "-n", type=int, default=4, help="Recent messages to preserve (default: 4)")
    parser.add_argument("--raw", action="store_true", help="Output compacted text only")
    parser.add_argument("--project", "-p", help="Filter to project directory pattern")
    parser.add_argument("--hierarchical", action="store_true", help="Compact all sessions under a project")
    parser.add_argument("--limit", "-l", type=int, default=10, help="Max sessions in hierarchical mode")
    parser.add_argument("--no-reducers", action="store_true", help="Disable typed reducer preprocessing")

    args = parser.parse_args()
    config_data = load_toml(args.config_file)
    defaults = load_flash_compact_defaults(config_data)
    view_config = CompactViewConfig(use_typed_reducers=not args.no_reducers)
    if args.hierarchical:
        if not args.project:
            print("Error: --hierarchical requires --project", file=sys.stderr)
            sys.exit(1)
        sessions = find_project_sessions(args.project, args.limit, sessions_dir=defaults.sessions_dir)
        if not sessions:
            print(f"No sessions found matching '{args.project}'", file=sys.stderr)
            sys.exit(1)

        # build a multi-session digest
        digest_parts = []
        for sp in sessions:
            title = read_session_title(sp)
            msgs = build_compact_messages_from_path(
                sp,
                query=args.query or "",
                preserve_recent=args.recent,
                config=view_config,
            )
            digest_parts.append(
                {
                    "role": "user",
                    "content": f"=== SESSION: {title} ({sp.stem[:8]}) ===",
                }
            )
            digest_parts.extend(msgs)
        result = morph_compact_messages(
            messages=digest_parts,
            query=args.query or "",
            compression_ratio=args.ratio,
            preserve_recent=0,
            include_markers=True,
            api_url=defaults.morph_api_url,
        )

        if args.raw:
            print(result["output"])
        else:
            usage = result.get("usage", {})
            print(f"# Hierarchical flash-compact: {len(sessions)} sessions", file=sys.stderr)
            print(f"# Input: {usage.get('input_tokens', '?')} tokens", file=sys.stderr)
            print(f"# Output: {usage.get('output_tokens', '?')} tokens", file=sys.stderr)
            print(f"# Ratio: {usage.get('compression_ratio', '?')}", file=sys.stderr)
            print(f"# Time: {usage.get('processing_time_ms', '?')}ms", file=sys.stderr)
            print(result["output"])
        return

    if not args.session:
        parser.print_help()
        sys.exit(1)

    session_path = resolve_session(args.session, defaults.sessions_dir)
    title = read_session_title(session_path)
    messages = build_compact_messages_from_path(
        session_path,
        query=args.query or "",
        preserve_recent=args.recent,
        config=view_config,
    )

    if not messages:
        print("No messages found in session", file=sys.stderr)
        sys.exit(1)

    result = morph_compact_messages(
        messages=messages,
        query=args.query or "",
        compression_ratio=args.ratio,
        preserve_recent=args.recent,
        include_markers=True,
        api_url=defaults.morph_api_url,
    )

    if args.raw:
        print(result["output"])
    else:
        usage = result.get("usage", {})
        print(f"# Session: {title}", file=sys.stderr)
        print(f"# ID: {session_path.stem}", file=sys.stderr)
        print(f"# Messages: {len(messages)}", file=sys.stderr)
        print(f"# Input: {usage.get('input_tokens', '?')} tokens", file=sys.stderr)
        print(f"# Output: {usage.get('output_tokens', '?')} tokens", file=sys.stderr)
        print(f"# Ratio: {usage.get('compression_ratio', '?')}", file=sys.stderr)
        print(f"# Time: {usage.get('processing_time_ms', '?')}ms", file=sys.stderr)
        print(result["output"])


if __name__ == "__main__":
    main()
