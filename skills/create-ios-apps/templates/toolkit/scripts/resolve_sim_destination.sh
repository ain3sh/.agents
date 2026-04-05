#!/usr/bin/env bash
set -euo pipefail

SIM_NAME=""
SIM_UDID=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --sim-name) SIM_NAME="$2"; shift 2 ;;
    --sim-udid) SIM_UDID="$2"; shift 2 ;;
    -h|--help)  echo "Usage: resolve_sim_destination.sh [--sim-name NAME] [--sim-udid UDID]"; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

if [[ -n "$SIM_UDID" ]]; then
  echo "platform=iOS Simulator,id=$SIM_UDID"
  exit 0
fi

SIM_NAME_ENV="$SIM_NAME" python3 - <<'PY'
import json
import os
import re
import subprocess
import sys

name = (os.environ.get("SIM_NAME_ENV") or "").strip()
name_lower = name.lower()

def runtime_version(runtime_key: str):
    match = re.search(r"iOS[- ](\d+)(?:[\.-](\d+))?", runtime_key)
    if not match:
        return (0, 0)
    return (int(match.group(1)), int(match.group(2) or 0))

VARIANT_RANK = {"pro max": 6, "pro": 5, "plus": 4, "air": 3, "": 2, "mini": 1, "e": 0}

def model_rank(device_name: str):
    number = 0
    match = re.search(r"iPhone\s+(\d+)", device_name)
    if match:
        number = int(match.group(1))
    lower = device_name.lower()
    suffix = ""
    for variant in ("pro max", "pro", "plus", "air", "mini"):
        if variant in lower:
            suffix = variant
            break
    if not suffix and re.search(r"iphone\s+\d+e\b", lower):
        suffix = "e"
    return (number, VARIANT_RANK.get(suffix, 0))

raw = subprocess.check_output(["xcrun", "simctl", "list", "devices", "-j"], text=True)
data = json.loads(raw)

candidates = []
for runtime_key, devices in data.get("devices", {}).items():
    for device in devices:
        if not device.get("isAvailable") or "iPhone" not in device.get("name", ""):
            continue
        candidates.append({
            "name": device["name"],
            "udid": device["udid"],
            "state": device.get("state", ""),
            "runtime_version": runtime_version(runtime_key),
        })

if not candidates:
    sys.exit(1)

if name and name_lower != "auto":
    matches = [c for c in candidates if c["name"] == name]
    if matches:
        booted = [c for c in matches if c["state"] == "Booted"]
        chosen = max(booted or matches, key=lambda c: c["runtime_version"])
        print(f"platform=iOS Simulator,id={chosen['udid']}")
        sys.exit(0)

booted = [c for c in candidates if c["state"] == "Booted"]
if booted:
    chosen = max(booted, key=lambda c: (c["runtime_version"], model_rank(c["name"])))
    print(f"platform=iOS Simulator,id={chosen['udid']}")
    sys.exit(0)

chosen = max(candidates, key=lambda c: (c["runtime_version"], model_rank(c["name"])))
print(f"platform=iOS Simulator,id={chosen['udid']}")
PY
