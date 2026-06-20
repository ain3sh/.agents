---
name: record-desktop-linux
description: Capture full-screen video and screenshots on Linux Wayland (KDE/KWin Plasma) via PipeWire ScreenCast + gpu-screen-recorder and spectacle. Use when you need a full-desktop recording or screenshot on a Wayland session, when cua-driver's record_video produces a black frame (x11grab on Xwayland), when wf-recorder/grim fail with "compositor doesn't support wlr-screencopy", or when wiring up droid-control / desktop-control capture on this machine.
---

# record-desktop-linux

One wrapper script with `start` / `stop` / `status` / `shot` / `verify` /
`doctor` subcommands. Picks the only capture path that actually works on
KDE/KWin Wayland (PipeWire portal for video, spectacle for stills), and refuses
to silently produce a black recording.

## TL;DR

```bash
S=~/.agents/skills/record-desktop-linux/scripts/record-desktop.sh
$S doctor                                  # one-time capability + token probe
$S start -s demo -o /tmp/demo.mp4          # detached recording
# ... drive the desktop / app ...
$S stop  -s demo                           # SIGINT, finalize, verify, print path
```

## When to use

- You need a **full-display** video or screenshot, not a per-window one.
- You're on a Wayland session (this box is KDE/KWin) where the obvious tools fail
  (see "Why other tools don't work here" at the bottom).
- You're orchestrating droid-control / desktop-control capture: keep cua-driver
  for actions and per-window `get_window_state --screenshot-out-file`, and use
  **this** for full-screen video + full-desktop stills.

If you only need per-window screenshots or AT-SPI actions, stay with
`cua-driver` directly. Don't reach for this skill unless full-display capture is
the goal.

## Prerequisites

```bash
sudo pacman -S gpu-screen-recorder spectacle ffmpeg
```

`doctor` reports the session type, the chosen capture source, every tool's
presence, the state of the portal restore token, and the state directory. Run
it first on any new machine.

## First-time setup (mandatory one-time human interaction)

The PipeWire ScreenCast portal **forces** the compositor to own surface
selection as a privacy boundary. An app cannot programmatically pick which
monitor/window to share on first grant; it can only ask, and KWin shows a
picker. There is no API to bypass this.

The cost is paid **once**. On the first `start`:

1. gpu-screen-recorder calls the portal's `SelectSources`/`Start` and blocks
   waiting for the response.
2. A KDE Plasma "Share your screen" dialog appears. Click your screen, then
   "Share". (If you don't see it, check the system tray; KDE sometimes parks
   it there.)
3. `-restore-portal-session yes` writes a token to
   `~/.config/gpu-screen-recorder/restore_token` (~36 bytes) that persists both
   the permission grant **and** the chosen surface.

Every subsequent `start` reuses that token and records **headlessly, no
dialog**. `doctor` reports the token's presence so you know which mode you're
in.

To re-pick the surface (or after KWin revokes the grant, e.g. across major
updates): `rm ~/.config/gpu-screen-recorder/restore_token`, then the next
`start` prompts once.

If you must run fully unattended with no token yet, you cannot. Either pay the
one-time interactive cost on the target machine first, or fall back to an X11
session (see bottom).

## Usage

```bash
S=~/.agents/skills/record-desktop-linux/scripts/record-desktop.sh

# --- video ---
$S start                                       # session "default", auto path, 30fps
$S start -s demo -f 60 -o /tmp/demo.mp4        # named session, 60fps, explicit path
$S start -s demo --no-pointer                  # hide cursor
$S start -s demo -w screen                     # force source (default: portal on Wayland, screen on X11)
$S status -s demo                              # running/stopped; exit 1 if stopped
$S stop  -s demo                               # SIGINT, finalize mp4, auto-verify

# --- stills (full desktop, headless) ---
$S shot -o /tmp/shot.png                       # full screen (default)
$S shot -o /tmp/cur.png -m monitor             # current monitor only
$S shot -o /tmp/win.png -m window              # active window
$S shot -o /tmp/p.png   --pointer              # include cursor

# --- safety check ---
$S verify /tmp/demo.mp4                        # rejects unplayable OR black clips
```

The default source auto-selects: `portal` on Wayland sessions
(`WAYLAND_DISPLAY` set), `screen` otherwise. Override with `-w` only if you
know better; on KWin Wayland `-w screen` fails with
`for_each_active_monitor_output_drm failed` because gpu-screen-recorder cannot
enumerate DRM outputs from a Wayland client.

## Sessions and state

Each `-s SESSION` is independent (own pidfile, output reference, log). Use
distinct names for concurrent recordings, identical names to address the same
recording across separate shells.

State lives at `$RECORD_DESKTOP_STATE_DIR/<session>/` (default
`$XDG_RUNTIME_DIR/record-desktop-linux/<session>/`, fallback
`/tmp/record-desktop-linux-$UID/<session>/`). Files:

| File | Purpose |
|---|---|
| `pid` | The detached recorder's PID; basis of `is_running` |
| `output` | Absolute path to the mp4 being written; read by `stop` |
| `log` | gpu-screen-recorder stdout+stderr; check on startup failures |

## Integration with droid-control / desktop-control

Use this skill for the **full-screen video** and **full-desktop screenshots**;
keep `cua-driver` for actions and per-window screenshots (`get_window_state
--screenshot-out-file`, which works fine). Hand the verified mp4 path to the
**compose** stage like any other clip.

```bash
RUN_ID="$(date +%s)-$$"; RUN_DIR="$(mktemp -d /tmp/droid-run-${RUN_ID}-XXXXXX)"
$S start -s "${RUN_ID}-desktop" -o "${RUN_DIR}/screen.mp4"
# ... drive the app via cua-driver actions; per-window pngs as needed ...
$S stop  -s "${RUN_ID}-desktop"   # verifies ${RUN_DIR}/screen.mp4
```

## Failure modes

| Symptom | Cause / fix |
|---|---|
| `start` hangs past ~20s on first ever run | Portal picker waiting. Look for the KDE "Share your screen" dialog (system tray if hidden). After one pick, the token makes future runs headless. |
| `verify ... looks black (mean luma 16)` | Wrong capture path. On Wayland the source must be `portal`; `x11grab`/`-w screen` produces this. Don't use cua-driver's `record_video` here. |
| `recorder exited during startup` (log printed) | Common: missing portal backend (install `xdg-desktop-portal-kde`), revoked grant (delete token, repick), or PipeWire down (`systemctl --user status pipewire`). |
| `for_each_active_monitor_output_drm failed` in log | gsr's direct DRM enumeration can't see KWin outputs. Harmless if source is `portal` (default); confirms `-w screen` won't work here. |
| mp4 plays for 0s / "moov atom not found" | Recorder was killed without SIGINT (SIGTERM/KILL skip finalization). Always stop via the helper, which uses SIGINT first and only escalates after 15s. |
| `pipewire negotiation` reached but file <100 bytes | Stopped before any frame was captured. Give portal handshake ~3-5s before sending stop; the helper already polls for negotiation completion. |
| spectacle opens a GUI window | The `-b` (background) flag isn't being passed. The helper sets it; if you call spectacle directly, always pass `-b -n -o FILE`. |
| Permission dialog reappears every run | `-restore-portal-session yes` not used, or token file missing/corrupt. The helper always passes it; check `~/.config/gpu-screen-recorder/restore_token` exists and is 36 bytes. |

## Why other tools don't work here (proven dead ends)

Future agents will be tempted to retry these. Don't.

- **cua-driver `record_video`** (any version through at least 0.5.7) uses ffmpeg
  `x11grab` on `$DISPLAY`. Under Wayland that only sees the empty Xwayland
  root, producing a black mp4 (mean luma ~16). cua-driver 0.5.7 added a
  native-Wayland backend (`CUA_DRIVER_RS_ENABLE_WAYLAND=1`), but it
  **explicitly excludes screen capture** ("still landing"), only targets
  **wlroots** compositors (sway/labwc/Hyprland), and only engages when
  `DISPLAY` is unset (here `DISPLAY=:0`). Upgrading will not fix this.
- **wf-recorder / grim** use `wlr-screencopy-unstable-v1`, which **KWin does
  not implement** ("compositor doesn't support the screen capture protocol").
  Same applies to wl-screenrec.
- **spectacle recording** (`-R s` / D-Bus `RecordScreen`): starts, but provides
  **no output-path argument**, **no D-Bus stop method** (only a GUI toggle /
  global shortcut), and reports the saved path only via an async
  `RecordingTaken` signal. Not automatable cleanly. Spectacle screenshots, by
  contrast, are perfectly headless via `-b -n -o FILE` and are what this skill
  uses for stills.
- **gpu-screen-recorder direct DRM** (`-w screen` on Wayland) fails enumeration.
  Only `-w portal` works on KWin Wayland.

## Alternative: switch to X11

If headless-from-first-run is a hard requirement (e.g., remote CI on this box),
log into a **Plasma X11** session. There `cua-driver record_video` and
`gpu-screen-recorder -w screen` both capture the real screen with no portal and
no token. This skill still works in that session: `start` auto-detects and
picks `screen`.

## Maintenance notes (for anyone editing the script)

- **Detachment.** `start` uses `setsid gsr ... </dev/null >log 2>&1 &` so the
  recorder survives the parent shell's exit. Without `setsid`, calling the
  helper from a tool that closes its shell (any separate `Execute` invocation)
  can SIGHUP the child.
- **Signal semantics.** gpu-screen-recorder finalizes the mp4's moov atom on
  **SIGINT only**. SIGTERM/SIGKILL skip finalization and produce an unplayable
  file. The stop path SIGINTs, polls up to 15s, then escalates to TERM at 15s
  and KILL at 20s; tune those windows before changing the signal.
- **ffmpeg `metadata=print` gotcha.** The signalstats metadata is emitted at
  ffmpeg's `info` log level. `-v error` (which we need to keep stderr clean)
  silently drops it. `verify` therefore writes the metadata via
  `metadata=print:file=$tmp` to a real file and parses that. Do not "simplify"
  this back to stdout/stderr capture; luma will read as `n/a` and the black
  guard will silently no-op.
- **Black threshold.** YUV black floor is ~16; real desktops sit at 40-90. The
  guard rejects mean luma < 18. Raising it risks false positives on legitimately
  dark themes; lowering it lets near-black captures through.
- **Audio.** Not captured. To opt in, add a flag that forwards to
  `gpu-screen-recorder -a default_output` (system audio) or `-a default_input`
  (mic).
