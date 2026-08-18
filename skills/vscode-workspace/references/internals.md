# Internals

Load this when debugging the machinery, changing the manager, or upgrading
versions. Day-to-day use needs only SKILL.md.

## Architecture

```
droid → @vscode-mcp/vscode-mcp-server (stdio, per session, stateless router)
      → per-workspace unix socket → MCP Bridge extension → VSCode API / LSP
```

The MCP server owns nothing: it discovers workspaces by scanning the socket
dir on every call, so workspaces spawned mid-session appear instantly — but
`mcp.json` changes (tool allowlist, version pin) need a new session.

Socket contract (shared with upstream `@vscode-mcp/vscode-mcp-ipc`):
`~/.local/share/yutengjing-vscode-mcp/vscode-mcp-<hash>.sock` where
`hash = md5(absolute workspace path)[:8]`; newline-delimited JSON
`{id, method, params}`. The manager speaks this protocol directly for
lifecycle ops (health, saveAll, closeWindow) so cleanup works with no MCP
server or droid session alive.

## Isolation model

- Per-workspace `--user-data-dir` (`instances/<hash>/`): own process tree, so
  a hard kill can never touch another workspace or a personal editor.
- Shared `--extensions-dir`: bridge + language extensions installed once by
  `setup`, reused read-only.
- Headless via `--ozone-platform=headless` — no display server at all.
- `code --wait` keeps the CLI process alive for the window's lifetime, so the
  spawned process group (spawned with `start_new_session`) tracks the
  workspace exactly and `killpg()` tears it down.
- Instance profiles are seeded with `security.workspace.trust.enabled: false`,
  `workbench.startupEditor: none`, telemetry/auto-update off before every
  spawn.

## State layout

```
~/.local/share/vscode-mcp-agent/
├── extensions/          # shared --extensions-dir
├── instances/<hash>/    # per-workspace --user-data-dir
├── registry/<hash>.json # {sessions[], pid, mode, spawned_at, last_seen}
└── logs/<hash>.log      # truncated per spawn
```

## Hooks (all gated in configs/droid.toml, all fail open)

- `pre_tool_use/vscode_auto_ensure.py` (`[hooks.pre_tool_use.vscode_auto_ensure]`):
  ensure before workspace-scoped `vscode:*` calls; injects/canonicalizes
  `workspace_path` via `updatedInput`; on cold spawns pre-warms the requested
  files or the git-modified set (`warm`, `warm_wait`). Warm path imports the
  manager in-process (~70ms); only spawns subprocess. A failed ensure denies
  with the real reason; hook errors pass through.
- `session_end/retire_vscode_workspaces.py` (`[hooks.session_end.vscode_workspaces]`):
  `reap --session <id>` — refcounted release; retires when the last owner
  leaves; always reaps dead instances/stale sockets.
- `session_start/reap_vscode_workspaces.py` (`[hooks.session_start.vscode_workspaces]`):
  `reap --idle-hours N` (default 12) — retires workspaces no session has
  ensured within the window. `last_seen` moves only on real use (ensure),
  never on reaper sweeps.
- `vscode-ws` command shim is installed by the `session_start/tool_wrappers`
  hook (`[hooks.session_start.tool_wrappers]`).

## Zombie taxonomy (what cleanup must catch)

- **Stale socket files** — self-heal: the bridge's `deactivate()` unlinks on
  clean exit; `list_workspaces`/`reap` unlink provably dead ones.
- **Crashpad handler** — detaches and reparents to init; caught by the
  instance-path cmdline sweep.
- **Language servers** (eslintServer.js, pylance, gopls) — cmdline points at
  the *shared* extensions dir, so per-workspace matching can't distinguish
  them; caught by the dead-`--clientProcessId` sweep instead (a dead owner
  pid proves orphaned; PID reuse can only make a dead owner look alive, which
  is the safe direction).

## Dead ends (do not retry)

- **xvfb-run / `DISPLAY` / `ELECTRON_OZONE_PLATFORM_HINT`**: code's `cli.js`
  strips `DISPLAY`/`ELECTRON_*`/`XDG_*` when spawning the GUI process — env
  vars never arrive, and on Wayland the window lands on the physical desktop.
  CLI args pass through untouched, which is why `--ozone-platform=headless`
  is the mechanism.
- **`--disable-workspace-trust`**: not a real CLI flag. Fresh profiles default
  to Restricted Mode, which silently disables semantic LSP (no TS type
  errors) — hence the settings seeding above.
- **Trusting first diagnostics on a cold instance**: language servers boot
  lazily; empty means "not analyzed yet". settle + warm cover the common case;
  `typescript.restartTsServer` is the unstick.
- **Kill-by-PID alone**: misses detached helpers. **`pkill code`**: hits
  unrelated instances (shared binary name).

## Versioning

Server and bridge release in lockstep under one tag. The pin lives in
`~/.factory/mcp.json` (`@vscode-mcp/vscode-mcp-server@X.Y.Z`); `setup` reads
it and installs `YuTengjing.vscode-mcp-bridge@X.Y.Z` to match, so the two
protocol sides cannot drift. Upgrade: bump the mcp.json pin, then
`vscode-ws setup --force`.
