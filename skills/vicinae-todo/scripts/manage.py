#!/usr/bin/env python3
"""
Vicinae Todo List CLI -- manages ~/.local/share/vicinae/support/store.raycast.todo-list/todo.json

Selectors:  positional arg is either a 0-based index (digits) or a case-insensitive
            title substring. Substring is matched across all sections unless --section
            narrows scope. Ambiguous matches print candidates and exit non-zero.

Commands:
  list   [-s SECTION] [--json]
  add    TITLE [...TITLE] [--pin] [-t TAG] [-p 1|2|3] [-d DUE]
  done   SELECTOR [-s SECTION]
  undo   SELECTOR
  pin    SELECTOR
  unpin  SELECTOR
  edit   SELECTOR NEWTITLE [-s SECTION]
  rm     SELECTOR [-s SECTION]
  clear  (wipes completed section)
"""

import argparse, datetime, json, re, sys, time
from pathlib import Path

FILE = Path.home() / ".local/share/vicinae/support/store.raycast.todo-list/todo.json"
SECTIONS = ("pinned", "todo", "completed")
PRI = {1: "low", 2: "mid", 3: "high"}


# ── data ──

def load():
    if not FILE.exists():
        FILE.parent.mkdir(parents=True, exist_ok=True)
        d = {"pinned": [], "todo": [], "completed": []}
        save(d)
        return d
    return json.loads(FILE.read_text())

def save(d):
    FILE.write_text(json.dumps(d))


# ── selector: index OR title substring ──

def resolve(data, sel, sections=None):
    """Return (section_key, index, item) or exit with error/ambiguity."""
    sections = sections or SECTIONS
    if sel.isdigit():
        idx = int(sel)
        for s in sections:
            if 0 <= idx < len(data[s]):
                return s, idx, data[s][idx]
        _die(f"index {idx} out of range in {', '.join(sections)}")
    needle = sel.lower()
    hits = []
    for s in sections:
        for i, it in enumerate(data[s]):
            if needle in it["title"].lower():
                hits.append((s, i, it))
    if len(hits) == 1:
        return hits[0]
    if not hits:
        _die(f"no item matching '{sel}'")
    lines = [f"  {s}[{i}] {it['title']}" for s, i, it in hits]
    _die(f"ambiguous '{sel}', matches:\n" + "\n".join(lines))


def _die(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


# ── due-date parsing: YYYY-MM-DD | +Nd | tomorrow | monday..sunday | today ──

_DAYS = {d: i for i, d in enumerate(("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"))}

def parse_due(s):
    if not s:
        return None
    s = s.strip().lower()
    today = datetime.date.today()
    if s == "today":
        dt = today
    elif s == "tomorrow":
        dt = today + datetime.timedelta(days=1)
    elif m := re.fullmatch(r"\+(\d+)d", s):
        dt = today + datetime.timedelta(days=int(m.group(1)))
    elif s in _DAYS:
        target = _DAYS[s]
        delta = (target - today.weekday()) % 7 or 7
        dt = today + datetime.timedelta(days=delta)
    else:
        try:
            dt = datetime.date.fromisoformat(s)
        except ValueError:
            _die(f"bad date '{s}' -- use YYYY-MM-DD, +Nd, tomorrow, today, or weekday name")
    return int(datetime.datetime.combine(dt, datetime.time()).timestamp() * 1000)


# ── formatting ──

def _fmt(i, it, sec):
    mark = {"completed": "x", "pinned": "*"}.get(sec, " ")
    extra = []
    if it.get("tag"):       extra.append(it["tag"])
    if it.get("priority"):  extra.append(f"!{PRI.get(it['priority'], '?')}")
    if it.get("dueDate"):
        extra.append("due:" + datetime.datetime.fromtimestamp(it["dueDate"] / 1000).strftime("%Y-%m-%d"))
    suffix = f"  ({', '.join(extra)})" if extra else ""
    return f"[{i}] [{mark}] {it['title']}{suffix}"


# ── commands ──

def cmd_list(args):
    data = load()
    secs = SECTIONS if args.section == "all" else (args.section,)
    if args.json:
        print(json.dumps({s: data[s] for s in secs}, indent=2))
        return
    total = 0
    for s in secs:
        items = data[s]
        if not items:
            continue
        print(f"\n{s.upper()} ({len(items)})")
        for i, it in enumerate(items):
            print(_fmt(i, it, s))
        total += len(items)
    if not total:
        print("empty")

def cmd_add(args):
    data = load()
    due = parse_due(args.due)
    sec = "pinned" if args.pin else "todo"
    for title in args.titles:
        it = {"title": title, "completed": False, "timeAdded": int(time.time() * 1000)}
        if args.tag:
            it["tag"] = args.tag if args.tag.startswith("#") else f"#{args.tag}"
        if args.priority:
            it["priority"] = args.priority
        if due:
            it["dueDate"] = due
        data[sec].append(it)
        print(f"+ {sec}: {title}")
    save(data)

def cmd_done(args):
    data = load()
    secs = (args.section,) if args.section else ("todo", "pinned")
    s, i, it = resolve(data, args.sel, secs)
    data[s].pop(i)
    it["completed"] = True
    data["completed"].append(it)
    save(data)
    print(f"done: {it['title']}")

def cmd_undo(args):
    data = load()
    s, i, it = resolve(data, args.sel, ("completed",))
    data["completed"].pop(i)
    it["completed"] = False
    data["todo"].append(it)
    save(data)
    print(f"undo: {it['title']}")

def cmd_pin(args):
    data = load()
    s, i, it = resolve(data, args.sel, ("todo",))
    data["todo"].pop(i)
    data["pinned"].append(it)
    save(data)
    print(f"pinned: {it['title']}")

def cmd_unpin(args):
    data = load()
    s, i, it = resolve(data, args.sel, ("pinned",))
    data["pinned"].pop(i)
    data["todo"].append(it)
    save(data)
    print(f"unpinned: {it['title']}")

def cmd_edit(args):
    data = load()
    secs = (args.section,) if args.section else SECTIONS
    s, i, it = resolve(data, args.sel, secs)
    old = it["title"]
    data[s][i]["title"] = args.title
    save(data)
    print(f"edit: {old} -> {args.title}")

def cmd_rm(args):
    data = load()
    secs = (args.section,) if args.section else SECTIONS
    s, i, it = resolve(data, args.sel, secs)
    data[s].pop(i)
    save(data)
    print(f"rm [{s}]: {it['title']}")

def cmd_clear(args):
    data = load()
    n = len(data["completed"])
    data["completed"] = []
    save(data)
    print(f"cleared {n} completed")


# ── main ──

def main():
    p = argparse.ArgumentParser(prog="todo")
    sub = p.add_subparsers(dest="cmd", required=True)

    ls = sub.add_parser("list")
    ls.add_argument("-s", "--section", default="all", choices=[*SECTIONS, "all"])
    ls.add_argument("--json", action="store_true")

    ad = sub.add_parser("add")
    ad.add_argument("titles", nargs="+")
    ad.add_argument("--pin", action="store_true")
    ad.add_argument("-t", "--tag")
    ad.add_argument("-p", "--priority", type=int, choices=[1, 2, 3])
    ad.add_argument("-d", "--due")

    dn = sub.add_parser("done")
    dn.add_argument("sel")
    dn.add_argument("-s", "--section", choices=["todo", "pinned"])

    ud = sub.add_parser("undo")
    ud.add_argument("sel")

    pn = sub.add_parser("pin")
    pn.add_argument("sel")

    up = sub.add_parser("unpin")
    up.add_argument("sel")

    ed = sub.add_parser("edit")
    ed.add_argument("sel")
    ed.add_argument("title")
    ed.add_argument("-s", "--section", choices=SECTIONS)

    rm = sub.add_parser("rm")
    rm.add_argument("sel")
    rm.add_argument("-s", "--section", choices=SECTIONS)

    sub.add_parser("clear")

    args = p.parse_args()
    {"list": cmd_list, "add": cmd_add, "done": cmd_done, "undo": cmd_undo,
     "pin": cmd_pin, "unpin": cmd_unpin, "edit": cmd_edit, "rm": cmd_rm,
     "clear": cmd_clear}[args.cmd](args)

if __name__ == "__main__":
    main()
