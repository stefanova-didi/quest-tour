#!/usr/bin/env bash
# Usage: scripts/smoke-package.sh dist/app.zip
# Unzips the package, installs requirements.txt into a fresh venv, runs startup.sh (alembic + uvicorn)
# against SQLite + local storage and checks the routes App Service will serve.
set -euo pipefail

ZIP="$(cd "$(dirname "${1:?usage: smoke-package.sh path/to/app.zip}")" && pwd)/$(basename "$1")"
PY="${SMOKE_PYTHON:-3.12}"   # production runtime; locally SMOKE_PYTHON=3.13 if 3.12 is unavailable
export PORT="${SMOKE_PORT:-8765}"   # startup.sh reads PORT, as on App Service
WORK="$(mktemp -d)"
SERVER_PID=""
cleanup() {
  if [ -n "$SERVER_PID" ]; then
    kill "$SERVER_PID" 2>/dev/null || true
    wait "$SERVER_PID" 2>/dev/null || true # let it release smoke.db before deleting
  fi
  rm -rf "$WORK" 2>/dev/null || true # Windows: a lingering child may still hold a file
}
trap cleanup EXIT

uv run --no-project --python "$PY" python -m zipfile -e "$ZIP" "$WORK/app"

for required in startup.sh requirements.txt alembic.ini alembic/env.py questtour/main.py \
  static/index.html VERSION; do
  [ -f "$WORK/app/$required" ] || { echo "package is missing $required" >&2; exit 1; }
done
VERSION="$(tr -d '[:space:]' <"$WORK/app/VERSION")"
[ -n "$VERSION" ] || { echo "package VERSION file is empty" >&2; exit 1; }
for forbidden in config tests .env; do
  [ ! -e "$WORK/app/$forbidden" ] || { echo "package must not contain $forbidden" >&2; exit 1; }
done

uv venv --quiet --python "$PY" "$WORK/venv"
VIRTUAL_ENV="$WORK/venv" uv pip install --quiet -r "$WORK/app/requirements.txt"
VENV_BIN="$WORK/venv/bin"
[ -d "$VENV_BIN" ] || VENV_BIN="$WORK/venv/Scripts"   # Windows venv layout

cd "$WORK/app"
PATH="$VENV_BIN:$PATH" \
  DATABASE_URL="sqlite:///./smoke.db" DATABASE_AUTH=password \
  STORAGE_BACKEND=local LOCAL_STORAGE_DIR=.smoke-storage \
  PUBLIC_BASE_URL="http://127.0.0.1:$PORT" STATIC_DIR=static \
  bash startup.sh >"$WORK/server.log" 2>&1 &
SERVER_PID=$!

BASE="http://127.0.0.1:$PORT"
for _ in $(seq 1 60); do
  curl -fsS "$BASE/api/health" >/dev/null 2>&1 && break
  if ! kill -0 "$SERVER_PID" 2>/dev/null; then
    cat "$WORK/server.log" >&2
    echo "server exited during startup" >&2
    exit 1
  fi
  sleep 1
done

expect() {
  local code
  code="$(curl -s -o /dev/null -w '%{http_code}' "$BASE$2")"
  if [ "$code" != "$1" ]; then
    echo "GET $2: expected $1, got $code" >&2
    cat "$WORK/server.log" >&2
    exit 1
  fi
}
expect 200 /api/health
expect 200 /
expect 200 /play/smoke-token
expect 404 /no/such/page
expect 404 /api/nope

# The running app must report the packaged version, and the SPA must carry the same one in its bundle.
health="$(curl -fsS "$BASE/api/health")"
case "$health" in
  *"\"version\":\"$VERSION\""*) ;;
  *) echo "/api/health does not report version $VERSION: $health" >&2; exit 1 ;;
esac
if ! grep -rqF -- "$VERSION" static/assets; then
  echo "the SPA bundle does not contain version $VERSION: build it with APP_VERSION=$VERSION" >&2
  exit 1
fi
echo "Package smoke test passed (version $VERSION)."
