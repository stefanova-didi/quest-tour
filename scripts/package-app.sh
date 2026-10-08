#!/usr/bin/env bash
# Build the App Service zip (zip deploy + Oryx remote build, no Docker):
#   questtour/ alembic/ alembic.ini startup.sh   backend code, run from the app root
#   requirements.txt                             exported from backend/uv.lock; Oryx installs it
#   static/                                      the built SPA (app setting STATIC_DIR=static)
#   VERSION                                      the build's version, reported by GET /api/health
# backend/config/ (teams.yaml holds live game tokens) and tests/ are deliberately left out.
# Usage: scripts/package-app.sh [out.zip]   — needs frontend/dist (run `npm run build` first).
# The version is $APP_VERSION, or else `git describe --tags --always --dirty` (a release tag such as
# v1.2.0, v1.2.0-3-g6dd4e31 past a tag, a bare commit hash before the first tag). Build the SPA with
# the same APP_VERSION in the environment so its footer matches (vite.config.ts falls back to the same
# `git describe`, so a build from the same checkout agrees without any variable).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${1:-$ROOT/dist/app.zip}"
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT

if [ ! -f "$ROOT/frontend/dist/index.html" ]; then
  echo "frontend/dist is missing: run 'npm run build' in frontend/ first" >&2
  exit 1
fi

APP_VERSION="${APP_VERSION:-$(git -C "$ROOT" describe --tags --always --dirty 2>/dev/null || echo dev)}"

cp -R "$ROOT/backend/questtour" "$ROOT/backend/alembic" "$ROOT/backend/alembic.ini" \
  "$ROOT/backend/startup.sh" "$STAGE/"
cp -R "$ROOT/frontend/dist" "$STAGE/static"
printf '%s\n' "$APP_VERSION" >"$STAGE/VERSION"
find "$STAGE" -name __pycache__ -type d -prune -exec rm -rf {} +
(cd "$ROOT/backend" && uv export --frozen --no-dev --no-hashes --no-emit-project \
  --output-file "$STAGE/requirements.txt" >/dev/null)

mkdir -p "$(dirname "$OUT")"
OUT="$(cd "$(dirname "$OUT")" && pwd)/$(basename "$OUT")"
rm -f "$OUT"
(cd "$STAGE" && uv run --no-project python -m zipfile -c "$OUT" \
  questtour alembic alembic.ini startup.sh requirements.txt static VERSION)
echo "Wrote $OUT (version $APP_VERSION)"
