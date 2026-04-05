#!/usr/bin/env bash
set -euo pipefail

APP_PATH=""
BACKGROUND=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --app-path)   APP_PATH="$2"; shift 2 ;;
    --background) BACKGROUND=1; shift ;;
    -h|--help)    echo "Usage: run_app_macos.sh --app-path PATH [--background]"; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

[[ -n "$APP_PATH" ]] || { echo "Missing --app-path" >&2; exit 1; }
[[ -d "$APP_PATH" ]] || { echo "App not found: $APP_PATH" >&2; exit 1; }

if [[ $BACKGROUND -eq 1 ]]; then
  open "$APP_PATH" &
else
  open -W "$APP_PATH"
fi
