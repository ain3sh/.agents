#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="$(cd "$SCRIPT_DIR/.." && pwd)/build"

if [[ -d "$BUILD_DIR" ]]; then
  rm -rf "$BUILD_DIR"
  echo "Cleaned $BUILD_DIR"
else
  echo "Nothing to clean."
fi
