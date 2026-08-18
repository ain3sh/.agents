---
name: vscode-workspace
description: "Spin up on-demand headless VSCode workspaces for live LSP diagnostics, symbol info, references, and workspace renames through the vscode MCP tools, then retire them with zero zombie processes or sockets. Use when you want editor-grade verification (vscode:get_diagnostics, get_symbol_lsp_info, get_references, rename_symbol, open_files) and no VSCode window is open for the project."
---

# VSCode Workspace

On-demand headless VSCode instances backing the `vscode:*` MCP tools (live LSP
diagnostics/symbols/renames). Nothing appears on the desktop; the lifecycle is
fully automated.

## Quickstart

Just call the tools — the first call spawns the workspace transparently:

```
vscode:get_diagnostics()                            # git-modified files, cwd project
vscode:get_diagnostics(workspace_path="/abs/path")  # explicit project
```

- `workspace_path` is optional: omitted → session cwd; non-canonical →
  rewritten to the resolved path before dispatch.
- A cold call blocks ~10-40s (editor boots, your target files get pre-warmed);
  warm calls cost ~70ms.
- Workspaces are tagged with your session and retired automatically when it
  ends. To free one early: `vscode-ws retire <path>`.

## Rules

- `workspace_path` must name the project **root**, not a child package or
  submodule. Prefer omitting it (cwd default) over constructing paths.
- Empty `__NOT_RECOMMEND__filePaths` = git-modified files; in a non-git
  directory that's silently zero files.
- Language server stuck on a fresh instance (empty results even after
  warm-up)? Unstick with `vscode:execute_command` → `typescript.restartTsServer`
  (or the language's equivalent).
- `rename_symbol` saves to disk. `execute_command` edits stay dirty in-memory
  until a save; `retire` saves all dirty editors before closing.
- Never `kill`/`pkill code` — instances share the binary name, so pattern
  kills can hit unrelated workspaces. `retire`/`reap` only signal
  cmdline-verified processes.

## Commands (`vscode-ws` is on PATH in sessions)

```bash
vscode-ws ensure <path> [--warm f ...] [--no-headless]  # create/reuse (idempotent)
vscode-ws retire <path>                                 # graceful close + cleanup
vscode-ws reap [--session ID | --all | --idle-hours N]  # zombie/stale cleanup
vscode-ws list                                          # registry + liveness
vscode-ws setup [--force]                               # one-time: dirs + extensions
```

Instance logs: `~/.local/share/vscode-mcp-agent/logs/<hash>.log`.
Internals, dead ends, hooks, versioning:
[references/internals.md](references/internals.md).

## Language support

Built in: TS/JS/HTML/CSS. Installed via `[tools.vscode-workspace].extensions`
in `configs/droid.toml`: Python+Pylance (auto-detects `.venv`), ESLint,
rust-analyzer, Go (needs `gopls` on PATH).
