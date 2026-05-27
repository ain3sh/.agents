---
name: mac-control
description: Control and navigate a logged-in macOS GUI session with upstream trycua/cua `cua-driver`. Use for macOS app automation, native dialogs, screenshots, UI inspection, clicking, typing, hotkeys, and any task where a Droid needs reliable computer-use control of macOS.
---

# macOS GUI Control with `cua-driver`

[`trycua/cua`](https://github.com/trycua/cua) wraps macOS Accessibility, ScreenCaptureKit, and event-posting APIs as scriptable tools, so a Droid can enumerate apps/windows, walk AX trees, capture screens, click, type, hotkey, scroll, drag, and drive real apps end-to-end.

SSH cannot reproduce GUI-bound behavior (Keychain/SecurityAgent prompts, permission sheets, focus-dependent input). Use SSH for install, status, and file-copy; use CUA for anything the user can see.

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/trycua/cua/main/libs/cua/installer/install.sh \
  | bash -s -- --no-modify-path
```

Installs `/Applications/CuaDriver.app` and `~/.local/bin/cua-driver`. Verify with `cua-driver --version` and `cua-driver doctor`.

## Permissions

In the GUI: System Settings → Privacy & Security → grant `CuaDriver.app` both **Accessibility** and **Screen Recording**. Then:

```bash
cua-driver status
cua-driver call check_permissions '{}'
```

Both must report granted. The first real screen capture may trigger an extra consent sheet — accept it.

## Start the daemon

Launch from the **visible logged-in Terminal** (SSH-launched daemons often fail to attach to the GUI session). Stop with `cua-driver stop`.

```bash
open -n -g -a CuaDriver --args serve
```

## Mental model

Every CUA workflow is a four-stage loop:

1. **Discover** — `list_apps` / `list_windows` → pick `(pid, window_id)`.
2. **Observe** — `get_window_state` for the AX tree; `screenshot` for raw pixels.
3. **Act** — semantic (AX `element_index`), pixel (`x`,`y`), keyboard (`press_key`/`hotkey`), or pasteboard (`pbcopy` + `Cmd+V`).
4. **Verify** — re-observe after every meaningful transition.

`element_index` is scoped per `(pid, window_id)` per `get_window_state` snapshot. Re-snapshot before each indexed action or it resolves against the wrong cache.

Prefer AX (semantic, precise) → fall back to pixel → fall back to keyboard/hotkey/pasteboard for surfaces AX can't reach (Terminal shells, some system sheets).

## Tool surface

`cua-driver list-tools` for the full inventory; `cua-driver describe <tool>` for the schema and behavior notes.

| Stage | Tools |
|---|---|
| Discover | `list_apps`, `list_windows` |
| Observe | `get_window_state`, `screenshot`, `zoom`, `get_cursor_position`, `get_screen_size` |
| Act | `click`, `double_click`, `right_click`, `type_text`, `set_value`, `press_key`, `hotkey`, `scroll`, `drag`, `move_cursor` |
| Config | `get_config`, `set_config`, `check_permissions` |

## Calls

All calls are `cua-driver call <tool> '<json>'`. The shorthand `call` below stands in for that prefix. Grouped to mirror the Discover → Observe → Act loop:

```bash
# Discover
call list_windows '{"on_screen_only":true}'
call list_windows '{"on_screen_only":false}'    # include hidden / off-space / minimized

# Observe
call get_window_state '{"pid":750,"window_id":45}'
call get_window_state '{"pid":750,"window_id":45,"query":"Allow"}'                 # filter AX tree to matching lines + ancestors
call get_window_state '{"pid":750,"window_id":45,"screenshot_out_file":"/tmp/w.png"}'
call screenshot       '{"out_file":"/tmp/screen.png"}'

# Act — semantic (requires a fresh get_window_state for the same window)
call click     '{"pid":750,"window_id":45,"element_index":3}'
call type_text '{"pid":750,"window_id":45,"element_index":1,"text":"hello"}'
call set_value '{"pid":750,"window_id":45,"element_index":2,"value":"42"}'

# Act — pixel / keyboard
call click     '{"pid":750,"window_id":45,"x":210,"y":145}'
call press_key '{"pid":365,"window_id":28,"key":"return"}'
call hotkey    '{"pid":365,"window_id":28,"keys":["cmd","v"]}'
call scroll    '{"pid":365,"window_id":28,"direction":"down"}'
call drag      '{"pid":365,"window_id":28,"from_x":100,"from_y":100,"to_x":400,"to_y":100}'
call zoom      '{"pid":365,"window_id":28,"x":0,"y":0,"width":400,"height":300}'
call move_cursor '{"x":640,"y":400}'
```

Capture mode is persistent config; switch when one path fails:

```bash
cua-driver config set capture_mode som      # AX tree + screenshot (default)
cua-driver config set capture_mode ax       # AX only — skips Screen Recording entirely
cua-driver config set capture_mode vision   # screenshot only — skips AX walk
```

## Patterns

**Reliable Terminal command entry** — when `type_text` / raw HID drops characters, route through the guest pasteboard:

```bash
printf '%s' 'your command' | pbcopy
call hotkey    '{"pid":<term-pid>,"window_id":<id>,"keys":["cmd","v"]}'
call press_key '{"pid":<term-pid>,"window_id":<id>,"key":"return"}'
```

**Native security / modal sheets** (SecurityAgent, permission prompts, auth dialogs) — these often report `is_on_screen:false` even when visible. Locate by process, then enumerate all windows:

```bash
pgrep -fl SecurityAgent
call list_windows '{"on_screen_only":false}'
call get_window_state '{"pid":<sa-pid>,"window_id":<id>}'
```

Typical Keychain sheet AX layout: `[1]` AXTextField (password), `[3]` "Always Allow", `[4]` "Deny", `[5]` "Allow". Only enter credentials in environments you own and were explicitly authorized to drive.

**Menu commands / app shortcuts** — pass `window_id` so AppKit routes the key equivalent to the target app instead of the frontmost one:

```bash
call hotkey '{"pid":835,"window_id":79,"keys":["cmd","q"]}'
```

**Backgrounded / off-space windows** — CUA acts on `(pid, window_id)` without raising. Enumerate with `on_screen_only:false`, target directly.

**Browser / Electron** — prefer a browser MCP for DOM work when available; otherwise CUA handles AX text, pixels, keys, and screenshots fine.

## Pitfalls

- Launch `CuaDriver.app` from the visible Terminal; SSH-launched daemons often miss the GUI identity and probes hang.
- `element_index` is per-snapshot per `(pid, window_id)`; re-snapshot before every indexed action.
- AX writes fail on some system sheets (`AXPress` returns `-25204`) — fall back to `press_key` / `hotkey` / pixel `click`.
- ScreenCaptureKit can fail in `som`/`vision` modes (e.g. SCK `-3801` on macOS 26.4.x); switch `capture_mode: ax` or retry.
- `on_screen_only:true` can omit visible system sheets — re-query with `false` when a known dialog is missing from results.
- Keep screenshots + raw tool output as evidence whenever GUI behavior is the thing under debug.
- For raw terminal byte / rendering proof, pair this with QEMU HID screenshots or the `true-input` macOS flow.
