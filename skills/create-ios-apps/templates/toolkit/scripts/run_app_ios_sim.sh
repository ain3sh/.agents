#!/usr/bin/env bash
set -euo pipefail

APP_PATH=""
SIM_NAME=""
BACKGROUND=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --app-path)   APP_PATH="$2"; shift 2 ;;
    --sim-name)   SIM_NAME="$2"; shift 2 ;;
    --background) BACKGROUND=1; shift ;;
    -h|--help)    echo "Usage: run_app_ios_sim.sh --app-path PATH --sim-name NAME [--background]"; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

[[ -n "$APP_PATH" ]] || { echo "Missing --app-path" >&2; exit 1; }
[[ -d "$APP_PATH" ]] || { echo "App not found: $APP_PATH" >&2; exit 1; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DESTINATION="$("$SCRIPT_DIR/resolve_sim_destination.sh" --sim-name "$SIM_NAME")"
[[ -n "$DESTINATION" ]] || { echo "No iOS Simulator found." >&2; exit 1; }
SIM_UDID="${DESTINATION##*id=}"

open -a Simulator >/dev/null 2>&1 || true
xcrun simctl boot "$SIM_UDID" >/dev/null 2>&1 || true
xcrun simctl bootstatus "$SIM_UDID" -b

BUNDLE_ID=$(/usr/libexec/PlistBuddy -c "Print:CFBundleIdentifier" "$APP_PATH/Info.plist")
xcrun simctl install "$SIM_UDID" "$APP_PATH"

if [[ $BACKGROUND -eq 1 ]]; then
  echo "Launching in background on simulator $SIM_UDID"
fi

xcrun simctl launch "$SIM_UDID" "$BUNDLE_ID"
