#!/usr/bin/env bash
set -euo pipefail

ACTION="build"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --action) ACTION="$2"; shift 2 ;;
    --)       shift; break ;;
    *)        break ;;
  esac
done

if [[ $# -eq 0 ]]; then
  echo "Usage: xcbuild.sh [--action build|test] -- <xcodebuild args>" >&2
  exit 1
fi

LOG_DIR="${LOG_DIR:-build/logs}"
mkdir -p "$LOG_DIR"

LOG_PATH="$LOG_DIR/${ACTION}.log"
RESULT_BUNDLE="$LOG_DIR/${ACTION}.xcresult"

if [[ -e "$LOG_PATH" || -d "$RESULT_BUNDLE" ]]; then
  STAMP="$(date '+%Y%m%d%H%M%S')"
  mkdir -p "$LOG_DIR/archive"
  [[ -e "$LOG_PATH" ]]      && mv "$LOG_PATH" "$LOG_DIR/archive/${ACTION}-${STAMP}.log"
  [[ -d "$RESULT_BUNDLE" ]] && mv "$RESULT_BUNDLE" "$LOG_DIR/archive/${ACTION}-${STAMP}.xcresult"
fi

CACHE_ROOT="${CACHE_ROOT:-$PWD/build/cache}"
CLANG_MODULE_CACHE="$CACHE_ROOT/clang/ModuleCache"
SWIFT_MODULE_CACHE="$CACHE_ROOT/swift/ModuleCache"
SPM_CACHE="$CACHE_ROOT/swiftpm"
SPM_SOURCES="$SPM_CACHE/SourcePackages"
BUILD_HOME="$PWD/build/home"
BUILD_TMP="$PWD/build/tmp"

mkdir -p "$CLANG_MODULE_CACHE" "$SWIFT_MODULE_CACHE" "$SPM_SOURCES" \
  "$BUILD_HOME/Library/Caches" "$BUILD_TMP"

export HOME="$BUILD_HOME" CFFIXED_USER_HOME="$BUILD_HOME" \
  XDG_CACHE_HOME="$CACHE_ROOT/xdg" TMPDIR="$BUILD_TMP"

FILTER_CMD=(cat)
if command -v xcbeautify >/dev/null 2>&1; then
  FILTER_CMD=(xcbeautify --is-ci)
fi

set +e
{
  xcodebuild "$@" \
    -clonedSourcePackagesDirPath "$SPM_SOURCES" \
    CLANG_MODULE_CACHE_PATH="$CLANG_MODULE_CACHE" \
    SWIFT_MODULE_CACHE_PATH="$SWIFT_MODULE_CACHE" \
    OTHER_SWIFT_FLAGS="\$(inherited) -Xfrontend -module-cache-path -Xfrontend $SWIFT_MODULE_CACHE -Xfrontend -disable-sandbox" \
    -resultBundlePath "$RESULT_BUNDLE"
} 2>&1 | tee "$LOG_PATH" | "${FILTER_CMD[@]}"
STATUS=${PIPESTATUS[0]}
set -e

if [[ $STATUS -ne 0 ]]; then
  echo "xcodebuild failed (status $STATUS). Log: $LOG_PATH" >&2
  exit $STATUS
fi

echo "xcodebuild succeeded. Log: $LOG_PATH"
