---
name: vicinae-todo
description: Manage the user's Vicinae Todo List from the terminal. Use when the user mentions todos, tasks, reminders, or when noting persistent cross-session work items.
---

# Vicinae Todo List

Syncs with the Vicinae launcher's Todo List extension.  
File: `~/.local/share/vicinae/support/store.raycast.todo-list/todo.json`  
Sections: `pinned`, `todo`, `completed`. Vicinae reads on launch; edits appear next open.

```
T="python3 ~/.agents/skills/vicinae-todo/scripts/manage.py"
```

## Selectors

All mutating commands accept a **selector**: a `0`-based index OR a case-insensitive title substring. Substring auto-searches across sections (narrow with `-s`). Ambiguous matches print candidates and exit non-zero.

## Commands

```bash
$T list                                  # all sections
$T list -s todo --json                   # JSON output, one section
$T add "Task A" "Task B"                 # batch add
$T add "Deploy" --pin -t ops -p 3 -d tomorrow
#   --due: YYYY-MM-DD | +Nd | today | tomorrow | weekday name
$T done "deploy"                         # match by title substring
$T done 0                                # or by index
$T undo 0                                # completed -> todo
$T pin "task a"                           # todo -> pinned
$T unpin 0                               # pinned -> todo
$T edit "task b" "Updated title"          # rename
$T rm "old item"                          # delete (any section)
$T clear                                 # wipe completed
```

Item fields: `title`, `completed`, `timeAdded` (ms), `tag?` (`#foo`), `priority?` (1=low 2=mid 3=high), `dueDate?` (ms).

Open in launcher: `vicinae 'vicinae://launch/store.raycast.todo-list/index'`
