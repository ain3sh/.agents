#!/usr/bin/env bash
# record-desktop.sh — ergonomic full-screen capture for Linux Wayland (KDE/KWin)
# Wraps gpu-screen-recorder (PipeWire portal) for video and spectacle for stills,
# because cua-driver's x11grab path records a black frame under Wayland.
#
# Subcommands:
#   start   [-s SESSION] [-o FILE] [-f FPS] [-w SOURCE] [--no-pointer]
#   stop    [-s SESSION]
#   status  [-s SESSION]
#   shot    -o FILE [-m full|monitor|window] [--pointer]
#   verify  FILE          # fails if the clip is unreadable or effectively black
#   doctor                # probe the environment for capability
#
# State (pidfile, output path, log) lives under:
#   $RECORD_DESKTOP_STATE_DIR  (default: $XDG_RUNTIME_DIR/record-wayland-desktop,
#                               falling back to /tmp/record-wayland-desktop-$UID)
set -euo pipefail

STATE_ROOT="${RECORD_DESKTOP_STATE_DIR:-${XDG_RUNTIME_DIR:-/tmp}/record-wayland-desktop}"
[ -n "${XDG_RUNTIME_DIR:-}" ] || STATE_ROOT="/tmp/record-wayland-desktop-$(id -u)"

err()  { printf '%s\n' "$*" >&2; }
die()  { err "error: $*"; exit 1; }
have() { command -v "$1" >/dev/null 2>&1; }

session_dir() { printf '%s/%s' "$STATE_ROOT" "${1:-default}"; }

# Pick the capture source gpu-screen-recorder should use.
# Wayland compositors require the PipeWire portal; X11 can grab "screen" directly.
default_source() {
  if [ -n "${WAYLAND_DISPLAY:-}" ]; then printf 'portal'; else printf 'screen'; fi
}

is_running() { # $1=pidfile
  local pid
  [ -f "$1" ] || return 1
  pid="$(cat "$1" 2>/dev/null || true)"
  [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null
}

cmd_start() {
  local session="default" output="" fps="30" source="" pointer="-cursor yes"
  while [ $# -gt 0 ]; do
    case "$1" in
      -s|--session) session="$2"; shift 2;;
      -o|--output)  output="$2";  shift 2;;
      -f|--fps)     fps="$2";     shift 2;;
      -w|--source)  source="$2";  shift 2;;
      --no-pointer) pointer="-cursor no"; shift;;
      *) die "start: unknown arg '$1'";;
    esac
  done

  have gpu-screen-recorder || die "gpu-screen-recorder not found (sudo pacman -S gpu-screen-recorder)"
  [ -n "$source" ] || source="$(default_source)"

  local dir; dir="$(session_dir "$session")"
  mkdir -p "$dir"
  local pidfile="$dir/pid" outfile_ref="$dir/output" logfile="$dir/log"

  if is_running "$pidfile"; then
    die "session '$session' already recording (pid $(cat "$pidfile")) -> $(cat "$outfile_ref" 2>/dev/null)"
  fi

  if [ -z "$output" ]; then
    output="$dir/recording-$(date +%Y%m%d-%H%M%S).mp4"
  fi
  mkdir -p "$(dirname "$output")"

  # restore-portal-session reuses the saved grant + surface choice, so after the
  # first (interactive) pick subsequent runs are headless.
  setsid gpu-screen-recorder \
      -w "$source" -restore-portal-session yes \
      -f "$fps" $pointer -o "$output" \
      </dev/null >"$logfile" 2>&1 &
  local pid=$!
  printf '%s' "$pid"     > "$pidfile"
  printf '%s' "$output"  > "$outfile_ref"

  # Wait until capture is actually live, not just spawned. For the portal path we
  # watch the log for negotiation; otherwise we confirm the process survives and
  # the file starts growing. First-ever portal use may block on a picker dialog.
  local waited=0 ok=0
  while [ "$waited" -lt 20 ]; do
    if ! kill -0 "$pid" 2>/dev/null; then
      err "--- recorder log ---"; tail -n 20 "$logfile" >&2 || true
      rm -f "$pidfile"
      die "recorder exited during startup (see log: $logfile)"
    fi
    if grep -qiE 'negotiation finished|start recording|replay' "$logfile" 2>/dev/null; then ok=1; break; fi
    if [ -s "$output" ]; then ok=1; break; fi
    sleep 0.5; waited=$((waited + 1))
  done
  [ "$ok" = 1 ] || err "warning: capture not confirmed after ${waited}s; check $logfile"

  printf 'recording: session=%s pid=%s source=%s\noutput: %s\nlog: %s\n' \
    "$session" "$pid" "$source" "$output" "$logfile"
}

cmd_stop() {
  local session="default"
  while [ $# -gt 0 ]; do
    case "$1" in
      -s|--session) session="$2"; shift 2;;
      *) die "stop: unknown arg '$1'";;
    esac
  done
  local dir; dir="$(session_dir "$session")"
  local pidfile="$dir/pid" outfile_ref="$dir/output"
  [ -f "$pidfile" ] || die "no recording state for session '$session'"
  local pid; pid="$(cat "$pidfile" 2>/dev/null || true)"
  local output; output="$(cat "$outfile_ref" 2>/dev/null || true)"

  if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
    kill -INT "$pid" 2>/dev/null || true
    local waited=0
    while kill -0 "$pid" 2>/dev/null; do
      sleep 0.5; waited=$((waited + 1))
      [ "$waited" -ge 30 ] && { kill -TERM "$pid" 2>/dev/null || true; }
      [ "$waited" -ge 40 ] && { kill -KILL "$pid" 2>/dev/null || true; break; }
    done
  else
    err "warning: process not running; finalizing from saved state"
  fi
  rm -f "$pidfile"

  [ -n "$output" ] && [ -f "$output" ] || die "output file missing: ${output:-<unknown>}"
  cmd_verify "$output"
}

cmd_status() {
  local session="default"
  while [ $# -gt 0 ]; do
    case "$1" in
      -s|--session) session="$2"; shift 2;;
      *) die "status: unknown arg '$1'";;
    esac
  done
  local dir; dir="$(session_dir "$session")"
  local pidfile="$dir/pid" outfile_ref="$dir/output"
  if is_running "$pidfile"; then
    printf 'running: session=%s pid=%s output=%s\n' \
      "$session" "$(cat "$pidfile")" "$(cat "$outfile_ref" 2>/dev/null)"
  else
    printf 'stopped: session=%s\n' "$session"
    return 1
  fi
}

cmd_shot() {
  local output="" mode="full" pointer=""
  while [ $# -gt 0 ]; do
    case "$1" in
      -o|--output) output="$2"; shift 2;;
      -m|--mode)   mode="$2";   shift 2;;
      --pointer)   pointer="-p"; shift;;
      *) die "shot: unknown arg '$1'";;
    esac
  done
  [ -n "$output" ] || die "shot: -o FILE is required"
  have spectacle || die "spectacle not found (sudo pacman -S spectacle)"
  mkdir -p "$(dirname "$output")"
  local mflag
  case "$mode" in
    full)    mflag="-f";;
    monitor) mflag="-m";;
    window)  mflag="-a";;
    *) die "shot: mode must be full|monitor|window";;
  esac
  spectacle -b -n $mflag $pointer -o "$output" >/dev/null 2>&1 || die "spectacle failed"
  # spectacle returns before the file is flushed; wait briefly for it.
  local waited=0
  while [ ! -s "$output" ] && [ "$waited" -lt 10 ]; do sleep 0.3; waited=$((waited + 1)); done
  [ -s "$output" ] || die "screenshot not written: $output"
  printf 'screenshot: %s (%s)\n' "$output" "$(du -h "$output" | cut -f1)"
}

cmd_verify() {
  local file="${1:-}"
  [ -n "$file" ] || die "verify: FILE is required"
  [ -f "$file" ] || die "verify: no such file: $file"
  have ffprobe || die "ffprobe not found (sudo pacman -S ffmpeg)"

  local dur
  dur="$(ffprobe -v error -select_streams v:0 -show_entries format=duration \
        -of default=nokey=1:noprint_wrappers=1 "$file" 2>/dev/null || true)"
  [ -n "$dur" ] && awk "BEGIN{exit !($dur>0)}" 2>/dev/null \
    || die "verify: $file has no playable video stream"

  # Sample mean luma; an all-black capture (the Wayland x11grab failure mode)
  # sits near the YUV black floor of ~16. metadata=print emits at ffmpeg's info
  # level, so route it to a file rather than fighting the log verbosity.
  local yavg meta
  meta="$(mktemp)"
  ffmpeg -v error -i "$file" \
    -vf "signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=$meta" \
    -frames:v 60 -f null /dev/null >/dev/null 2>&1 || true
  yavg="$(awk -F= '/YAVG/{s+=$2;n++} END{if(n)printf "%.1f", s/n}' "$meta" 2>/dev/null)"
  rm -f "$meta"
  if [ -n "$yavg" ] && awk "BEGIN{exit !($yavg<18)}" 2>/dev/null; then
    die "verify: $file looks black (mean luma $yavg) — capture source likely wrong"
  fi
  printf 'ok: %s  duration=%ss  luma=%s  size=%s\n' \
    "$file" "$dur" "${yavg:-n/a}" "$(du -h "$file" | cut -f1)"
}

cmd_doctor() {
  printf 'session type: %s\n' "${XDG_SESSION_TYPE:-unknown}"
  printf 'WAYLAND_DISPLAY=%s  DISPLAY=%s\n' "${WAYLAND_DISPLAY:-}" "${DISPLAY:-}"
  printf 'default source: %s\n' "$(default_source)"
  for b in gpu-screen-recorder spectacle ffprobe ffmpeg; do
    if have "$b"; then printf '  %-22s ok (%s)\n' "$b" "$(command -v "$b")"
    else printf '  %-22s MISSING\n' "$b"; fi
  done
  local token="${XDG_CONFIG_HOME:-$HOME/.config}/gpu-screen-recorder/restore_token"
  if [ -f "$token" ]; then printf 'portal restore token: present (headless re-records)\n'
  else printf 'portal restore token: absent (first start will prompt for surface)\n'; fi
  printf 'state dir: %s\n' "$STATE_ROOT"
}

main() {
  local sub="${1:-}"; shift || true
  case "$sub" in
    start)  cmd_start  "$@";;
    stop)   cmd_stop   "$@";;
    status) cmd_status "$@";;
    shot)   cmd_shot   "$@";;
    verify) cmd_verify "$@";;
    doctor) cmd_doctor "$@";;
    ""|-h|--help)
      awk 'NR>1 && /^#/{sub(/^# ?/,""); print; next} NR>1{exit}' "$0";;
    *) die "unknown subcommand '$sub' (try: start stop status shot verify doctor)";;
  esac
}

main "$@"
