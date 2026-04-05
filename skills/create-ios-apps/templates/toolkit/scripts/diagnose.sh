#!/usr/bin/env bash
set -euo pipefail

check() {
  if command -v "$1" >/dev/null 2>&1; then echo "ok: $1"; else echo "missing: $1"; fi
}

echo "Scheme:      ${APP_SCHEME:-unknown}"
echo "Platform:    ${APP_PLATFORM:-unknown}"
echo "Destination: ${APP_DESTINATION:-unknown}"
echo "Project:     ${PROJECT:-unknown}"
echo "Workspace:   ${WORKSPACE:-none}"
echo ""

if command -v xcode-select >/dev/null 2>&1; then echo "xcode-select: $(xcode-select -p)"; fi
if command -v xcodebuild >/dev/null 2>&1; then xcodebuild -version; fi
echo ""
check xcrun
check python3
check xcodegen
check xcbeautify
check jq
