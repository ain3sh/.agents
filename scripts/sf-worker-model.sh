#!/usr/bin/env bash
# Pins the main model of Software Factory worker sessions on template computers.
# A template run starts in ~/.factory/software-factory/workstreams/<slug>, and
# hydration restores only memory/, scripts/ and skills/ there, so the project
# settings that beat the user default must be baked into the image. Called from
# the ain3sh-dev template setup script; takes effect on the next template build.
set -euo pipefail
for slug in pr-shepherd; do
  dir="$HOME/.factory/software-factory/workstreams/$slug/.factory"
  mkdir -p "$dir"
  printf '%s\n' '{"sessionDefaultSettings":{"model":"claude-fable-5.1","reasoningEffort":"high"}}' >"$dir/settings.json"
done
