#!/usr/bin/env sh
set -eu

if [ -z "${TMPDIR:-}" ] && [ -d "/dev/shm" ] && [ -w "/dev/shm" ]; then
  export TMPDIR="/dev/shm"
fi

exec "$@"
