#!/usr/bin/env bash
set -euo pipefail

now_utc() {
  date -u '+%Y-%m-%dT%H:%M:%SZ'
}

{
  echo ""
  echo "==================== SESSIONSTART DEBUG $(now_utc) ===================="
  echo "hook pid=$$ ppid=${PPID:-}" 
  echo "cwd=$(pwd)"
  echo "whoami=$(whoami 2>/dev/null || true) uid=$(id -u 2>/dev/null || true) gid=$(id -g 2>/dev/null || true)"

  echo ""
  # SessionStart input should be small; still cap output to avoid giant logs.
  stdin_payload="$(cat || true)"
  echo "-- hook stdin (first 8KB) --"
  echo "${stdin_payload:0:8192}"

  # Droid may provide an env-file path via hook input JSON rather than exporting DROID_ENV_FILE.
  env_file_from_stdin=""
  if command -v python3 >/dev/null 2>&1; then
    env_file_from_stdin="$(
      STDIN_PAYLOAD="$stdin_payload" python3 - <<'PY' 2>/dev/null || true
import json, os

raw = os.environ.get("STDIN_PAYLOAD", "")
try:
  data = json.loads(raw) if raw else {}
except Exception:
  data = {}

# Prefer explicit droid field if present; fall back to CLAUDE_ENV_FILE if that's what Droid emits.
val = (
  data.get("DROID_ENV_FILE")
  or data.get("droidEnvFile")
  or data.get("CLAUDE_ENV_FILE")
  or data.get("claudeEnvFile")
  or ""
)

print(val)
PY
    )"
  fi

  echo ""
  echo "-- env file discovery --"
  echo "DROID_ENV_FILE(env)=${DROID_ENV_FILE:-}"
  echo "CLAUDE_ENV_FILE(env)=${CLAUDE_ENV_FILE:-}"
  echo "envFile(from stdin json)=${env_file_from_stdin:-}"

  echo ""
  echo "-- key env vars --"
  echo "FACTORY_PROJECT_DIR=${FACTORY_PROJECT_DIR:-}"
  echo "FACTORY_USER_DIR=${FACTORY_USER_DIR:-}"
  echo "DROID_PROJECT_DIR=${DROID_PROJECT_DIR:-}"
  echo "DROID_ENV_FILE=${DROID_ENV_FILE:-}"
  echo "PATH=${PATH:-}"

  echo ""
  echo "-- env file contents (best-effort) --"
  env_file_to_read="${DROID_ENV_FILE:-${CLAUDE_ENV_FILE:-${env_file_from_stdin:-}}}"
  if [ -n "$env_file_to_read" ]; then
    echo "env_file_to_read=$env_file_to_read"
    if [ -f "$env_file_to_read" ]; then
      echo "env_file_exists=true"
      echo "(first 200 lines)"
      sed -n '1,200p' "$env_file_to_read" || true
      echo "(PATH-related lines)"
      rg -n '^\s*(export\s+)?PATH=' "$env_file_to_read" 2>/dev/null || true
    else
      echo "env_file_exists=false"
    fi
  else
    echo "env_file_to_read="
  fi

  echo ""
  echo "-- tool availability --"
  for bin in sh bash zsh python3 node npm npx openskills; do
    if command -v "$bin" >/dev/null 2>&1; then
      echo "found $bin at: $(command -v "$bin")"
    else
      echo "missing $bin"
    fi
  done

  echo ""
  echo "-- versions (best-effort) --"
  node --version 2>/dev/null || echo "node --version failed"
  npm --version 2>/dev/null || echo "npm --version failed"
  npx --version 2>/dev/null || echo "npx --version failed"
  openskills --version 2>/dev/null || echo "openskills --version failed"

  echo "======================================================================="
}

exit 0
