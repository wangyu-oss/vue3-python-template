#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

ROOT="$(pwd)"
PY_DIR="$ROOT/python"
WEB_DIR="$ROOT/web"
VENV_PY="$PY_DIR/myenv/bin/python"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 not found"
  exit 1
fi
if ! command -v npm >/dev/null 2>&1; then
  echo "npm not found"
  exit 1
fi

if [ ! -x "$VENV_PY" ]; then
  python3 -m venv "$PY_DIR/myenv"
fi

if ! "$VENV_PY" -c "import django,corsheaders" >/dev/null 2>&1; then
  "$VENV_PY" -m pip install -r "$PY_DIR/requirements.txt"
fi

if [ ! -d "$WEB_DIR/node_modules" ]; then
  (cd "$WEB_DIR" && npm install)
fi

(cd "$PY_DIR" && "$VENV_PY" manage.py runserver 0.0.0.0:8000 --noreload) &
BACK_PID=$!
(cd "$WEB_DIR" && npm run dev) &
WEB_PID=$!

trap 'kill $BACK_PID $WEB_PID 2>/dev/null || true' INT TERM
wait
