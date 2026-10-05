#!/usr/bin/env bash
# Local no-Docker dev run: SQLite + local file storage, backend and frontend together.
# Writes backend/.env on first run (gitignored; env vars win over it and the deploy
# package never includes it), then runs the README's no-Docker steps:
# uv sync → alembic → sync-config → uvicorn --reload, plus the Vite dev server.
# Runs in the foreground; Ctrl-C stops both. Every output line is tagged
# [backend] / [frontend] so the interleaved logs stay readable.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# One tagger for both phases: setup banners and piped command output share it.
# $'..' makes these real ESC sequences; printf only interprets escapes in its
# format string, so arguments must carry actual control characters.
C_BACKEND=$'\033[36m'    # cyan
C_FRONTEND=$'\033[32m'   # green
banner() { printf '%s[%s]\033[0m %s\n' "$2" "$1" "$3"; }
# Prefixes every piped line with the component it came from; fflush keeps tags in order.
label_output() {
  awk -v tag="$1" -v color="$2" '{ printf "%s[%s]\033[0m %s\n", color, tag, $0; fflush() }'
}

missing=()
command -v uv >/dev/null || missing+=("uv")
command -v npm >/dev/null || missing+=("npm")
if [ "${#missing[@]}" -gt 0 ]; then
  echo "[dev] Missing on PATH: ${missing[*]} (see README prerequisites)." >&2
  exit 1
fi

if [ ! -f "$ROOT/backend/.env" ]; then
  cat > "$ROOT/backend/.env" <<'EOF'
DATABASE_URL=sqlite:///./dev.db
HOST_ID=default
PUBLIC_BASE_URL=http://localhost:5173
STORAGE_BACKEND=local
LOCAL_STORAGE_DIR=.storage
CONFIG_DIR=config
EOF
  banner backend "$C_BACKEND" "==> wrote backend/.env (SQLite, local file storage)"
fi

cd "$ROOT/backend"
banner backend "$C_BACKEND" "==> uv sync"
if ! uv sync 2>&1 | label_output backend "$C_BACKEND"; then
  banner backend "$C_BACKEND" "==> uv sync failed, retrying with Python 3.13"
  uv sync --python 3.13 2>&1 | label_output backend "$C_BACKEND"
fi

banner backend "$C_BACKEND" "==> alembic upgrade head"
uv run alembic upgrade head 2>&1 | label_output backend "$C_BACKEND"

banner backend "$C_BACKEND" "==> sync-config (prints the team game links)"
# Keep the raw output: the game links are re-printed in the final summary.
sync_output="$(uv run sync-config 2>&1)"
printf '%s\n' "$sync_output" | label_output backend "$C_BACKEND"

cd "$ROOT/frontend"
banner frontend "$C_FRONTEND" "==> npm install (skipped when node_modules exists)"
if [ ! -d node_modules ]; then
  npm install 2>&1 | label_output frontend "$C_FRONTEND"
fi

echo
printf '[dev] %s\n' \
  "==> Starting backend on :8000 and frontend on :5173." \
  "==> Ctrl-C stops both servers." \
  ""
printf '[dev] Game links:\n'
printf '%s\n' "$sync_output" | grep 'http' | sed 's/^[[:space:]]*//' | while IFS= read -r link; do
  printf '[dev]   %s\n' "$link"
done

# Job control in a script gives each background job its own process group, so a single
# negative-PID kill takes down the whole pipeline (server + label filter). With groups
# separate, Ctrl-C reaches this script only, and the trap forwards it to both groups.
set -m

start_backend() {
  cd "$ROOT/backend"
  uv run uvicorn questtour.main:create_app --factory --reload 2>&1 \
    | label_output backend "$C_BACKEND"
}
start_frontend() {
  cd "$ROOT/frontend"
  npm run dev 2>&1 | label_output frontend "$C_FRONTEND"
}

start_backend & backend_pid=$!
start_frontend & frontend_pid=$!

cleaned=0
cleanup() {
  ((cleaned)) && return 0
  cleaned=1
  echo
  echo "[dev] ==> Stopping backend and frontend..."
  kill -- "-$backend_pid" "-$frontend_pid" 2>/dev/null || true
  wait
}
trap cleanup INT TERM EXIT
wait
