#!/usr/bin/env bash
# Project settings for Software Factory worker sessions on template computers.
# A template run starts in ~/.factory/software-factory/workstreams/<slug>, and
# hydration restores only memory/, scripts/ and skills/ there, so the project
# settings that beat the user defaults must be baked into the image. Called from
# the ain3sh-dev template setup script; takes effect on the next template build.
#
# - sessionDefaultSettings pins workers to Fable 5.1.
# - cloudSessionSync overrides the user-level `false`: the backend activity
#   coordinator judges a worker alive by its cloud session, and requeues the
#   activity (while the original keeps running) when that session is missing.
set -euo pipefail
for slug in pr-shepherd ownership-incident-fixer; do
  dir="$HOME/.factory/software-factory/workstreams/$slug/.factory"
  mkdir -p "$dir"
  printf '%s\n' '{"cloudSessionSync":true,"sessionDefaultSettings":{"model":"claude-fable-5.1","reasoningEffort":"high"}}' >"$dir/settings.json"
done
