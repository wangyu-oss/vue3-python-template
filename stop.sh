#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

for port in 8000 5173; do
  if command -v lsof >/dev/null 2>&1; then
    pids=$(lsof -ti tcp:"$port" || true)
    if [ -n "${pids}" ]; then
      kill $pids || true
      echo "freed $port"
    else
      echo "port $port already free"
    fi
  else
    echo "lsof not found, skip port $port"
  fi
done
