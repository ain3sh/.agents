#!/usr/bin/env bash
# Project settings for Software Factory worker sessions on template computers.
# A template run starts in ~/.factory/software-factory/workstreams/<slug>, and
# hydration restores only memory/, scripts/ and skills/ there, so the project
# settings that beat the user defaults must be baked into the image. Called from
# the ain3sh-dev template setup script; takes effect on the next template build.
#
# sessionDefaultSettings pins workers to Fable 5.1. Cloud session sync comes
# from the user settings the template writes; the activity coordinator needs it
# to see a worker's session as alive.
set -euo pipefail
for slug in pr-shepherd ownership-incident-fixer re-review; do
  dir="$HOME/.factory/software-factory/workstreams/$slug/.factory"
  mkdir -p "$dir"
  printf '%s\n' '{"sessionDefaultSettings":{"model":"claude-fable-5.1","reasoningEffort":"high"}}' >"$dir/settings.json"
done
