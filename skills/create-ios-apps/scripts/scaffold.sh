#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scaffold.sh --mode new|adopt --output PATH [options]

New project:
  --name NAME               App name (required)
  --bundle-id ID            Bundle identifier (required)
  --platform ios|macos      Target platform (required)
  --ui swiftui|uikit|appkit UI framework (default: swiftui)
  --deployment-target VER   (default: 18.0 iOS, 15.4 macOS)
  --sim-name NAME           iOS simulator (default: auto)

Adopt existing project:
  --name NAME               Scheme name (auto-detected from .xcodeproj if omitted)
  --platform ios|macos      Target platform (required)

Common:
  --force                   Overwrite existing Makefile and scripts
  --dry-run                 Preview without writing files
USAGE
}

MODE=""
APP_NAME=""
BUNDLE_ID=""
PLATFORM=""
UI="swiftui"
OUTPUT=""
DEPLOYMENT_TARGET=""
SIM_NAME=""
FORCE=0
DRY_RUN=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode)              MODE="$2"; shift 2 ;;
    --name)              APP_NAME="$2"; shift 2 ;;
    --bundle-id)         BUNDLE_ID="$2"; shift 2 ;;
    --platform)          PLATFORM="$2"; shift 2 ;;
    --ui)                UI="$2"; shift 2 ;;
    --output)            OUTPUT="$2"; shift 2 ;;
    --deployment-target) DEPLOYMENT_TARGET="$2"; shift 2 ;;
    --sim-name)          SIM_NAME="$2"; shift 2 ;;
    --force)             FORCE=1; shift ;;
    --dry-run)           DRY_RUN=1; shift ;;
    -h|--help)           usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage; exit 1 ;;
  esac
done

[[ "$MODE" == "new" || "$MODE" == "adopt" ]] || { echo "Invalid --mode (expected new or adopt)." >&2; exit 1; }
[[ -n "$OUTPUT" ]] || { echo "Missing --output." >&2; exit 1; }
[[ "$PLATFORM" == "ios" || "$PLATFORM" == "macos" ]] || { echo "Invalid --platform (expected ios or macos)." >&2; exit 1; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
RENDER="$SCRIPT_DIR/render_template.py"

# --- New project: scaffold from XcodeGen template ---
if [[ "$MODE" == "new" ]]; then
  [[ -n "$APP_NAME" ]]  || { echo "Missing --name." >&2; exit 1; }
  [[ -n "$BUNDLE_ID" ]] || { echo "Missing --bundle-id." >&2; exit 1; }

  case "$UI" in
    swiftui) ;;
    uikit)   [[ "$PLATFORM" == "ios" ]]   || { echo "UIKit requires --platform ios." >&2; exit 1; } ;;
    appkit)  [[ "$PLATFORM" == "macos" ]]  || { echo "AppKit requires --platform macos." >&2; exit 1; } ;;
    *) echo "Invalid --ui (expected swiftui, uikit, or appkit)." >&2; exit 1 ;;
  esac

  if [[ -z "$DEPLOYMENT_TARGET" ]]; then
    [[ "$PLATFORM" == "ios" ]] && DEPLOYMENT_TARGET="18.0" || DEPLOYMENT_TARGET="15.4"
  fi
  [[ -z "$SIM_NAME" && "$PLATFORM" == "ios" ]] && SIM_NAME="auto"

  TEMPLATE_DIR="$SKILL_ROOT/templates/xcodegen/${PLATFORM}-${UI}"
  [[ -d "$TEMPLATE_DIR" ]] || { echo "Template not found: $TEMPLATE_DIR" >&2; exit 1; }

  if [[ -d "$OUTPUT" && -n "$(ls -A "$OUTPUT" 2>/dev/null)" ]]; then
    echo "Output directory is not empty: $OUTPUT" >&2
    exit 1
  fi

  if [[ $DRY_RUN -eq 1 ]]; then
    echo "[dry-run] Scaffold $PLATFORM/$UI project '$APP_NAME' -> $OUTPUT"
    echo "[dry-run] Install Makefile + build scripts"
    exit 0
  fi

  mkdir -p "$OUTPUT"
  python3 "$RENDER" --src "$TEMPLATE_DIR" --dst "$OUTPUT" \
    --var APP_NAME="$APP_NAME" \
    --var BUNDLE_ID="$BUNDLE_ID" \
    --var DEPLOYMENT_TARGET="$DEPLOYMENT_TARGET" \
    --var SIM_NAME="$SIM_NAME" \
    --var PLATFORM="$PLATFORM"

  (cd "$OUTPUT" && xcodegen generate)
fi

# --- Adopt existing project ---
if [[ "$MODE" == "adopt" ]]; then
  [[ -d "$OUTPUT" ]] || { echo "Directory not found: $OUTPUT" >&2; exit 1; }

  if [[ -z "$APP_NAME" ]]; then
    detected="$(ls "$OUTPUT"/*.xcodeproj 2>/dev/null | head -n 1 || true)"
    [[ -n "$detected" ]] && APP_NAME="$(basename "$detected" .xcodeproj)"
  fi
  [[ -n "$APP_NAME" ]] || { echo "Could not detect app name. Pass --name explicitly." >&2; exit 1; }
  [[ -z "$SIM_NAME" && "$PLATFORM" == "ios" ]] && SIM_NAME="auto"
fi

# --- Install Makefile + build scripts ---
if [[ -e "$OUTPUT/Makefile" && $FORCE -eq 0 ]]; then
  echo "Makefile already exists at $OUTPUT/Makefile. Use --force to overwrite." >&2
  exit 1
fi

if [[ $DRY_RUN -eq 1 ]]; then
  echo "[dry-run] Install Makefile + build scripts -> $OUTPUT"
  exit 0
fi

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

python3 "$RENDER" --src "$SKILL_ROOT/templates/toolkit" --dst "$TMP_DIR" \
  --var APP_NAME="$APP_NAME" \
  --var PLATFORM="$PLATFORM" \
  --var SIM_NAME="${SIM_NAME:-}"

cp "$TMP_DIR/Makefile" "$OUTPUT/Makefile"
mkdir -p "$OUTPUT/scripts"
cp -R "$TMP_DIR/scripts/." "$OUTPUT/scripts/"
find "$OUTPUT/scripts" -name '*.sh' -exec chmod +x {} +

echo ""
echo "Project ready: $OUTPUT"
echo ""
echo "Next:"
echo "  cd $OUTPUT"
echo "  make diagnose"
echo "  make build"
echo "  make test"
echo "  make run"
