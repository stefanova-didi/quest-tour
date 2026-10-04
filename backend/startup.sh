#!/usr/bin/env bash
# App Service startup (clarify: migrations run here, before uvicorn). Oryx runs this from the
# extracted app root with its virtualenv active; every path below is relative to that root.
set -euo pipefail

# Trust X-Forwarded-* from App Service's front end. Set through uvicorn's env var rather than
# `--forwarded-allow-ips '*'`: a literal * argument gets glob-expanded by Windows Python launchers,
# which breaks the local package smoke test.
export FORWARDED_ALLOW_IPS="${FORWARDED_ALLOW_IPS:-*}"

python -m alembic upgrade head
exec python -m uvicorn questtour.main:create_app --factory \
  --host 0.0.0.0 --port "${PORT:-8000}" --proxy-headers
