#!/usr/bin/env sh
set -eu
if [ ! -x ".venv/bin/python" ]; then
  echo "Missing .venv. Create it and install requirements-release.txt first." >&2
  exit 2
fi
exec .venv/bin/python launch_alpha.py "$@"
