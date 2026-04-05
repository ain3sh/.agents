#!/usr/bin/env bash
set -euo pipefail

MISSING=0

check_required() {
  if command -v "$1" >/dev/null 2>&1; then
    echo "ok: $1"
  else
    echo "MISSING: $1"
    MISSING=1
  fi
}

check_optional() {
  if command -v "$1" >/dev/null 2>&1; then
    echo "ok: $1 (optional)"
  else
    echo "not found: $1 (optional)"
  fi
}

echo "Checking toolchain..."
echo ""

if command -v xcode-select >/dev/null 2>&1; then
  echo "xcode-select: $(xcode-select -p)"
else
  echo "MISSING: xcode-select"
  MISSING=1
fi

if command -v xcodebuild >/dev/null 2>&1; then
  xcodebuild -version
else
  echo "MISSING: xcodebuild"
  MISSING=1
fi

check_required xcrun
check_required python3
check_required xcodegen
check_optional xcbeautify
check_optional jq

echo ""
if [[ $MISSING -ne 0 ]]; then
  echo "Required tools missing."
  echo "  Xcode:    https://xcodereleases.com"
  echo "  XcodeGen: brew install xcodegen"
  exit 1
fi

echo "All required tools found."
