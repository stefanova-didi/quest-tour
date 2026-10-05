# AGENTS.md — guidance for AI coding agents

Quest City Tour: a mobile-first web app for guided city quests. Admins define landmarks, games and
teams in YAML; teams get a private link and play a sequence of riddles + landmark photos against a
server-side clock, with a leaderboard at the end. Specs are the source of truth for behaviour.

## Repository layout

```
specs/                      Requirements, technical spec, frontend design brief (READ BEFORE CHANGES)
frontend/                   React 19 + TypeScript + Vite SPA (the player app)
frontend/src/
  api/                      HTTP client (client.ts) and API types (types.ts)
  game/                     useGame.ts (state machine + 60 s polling), selectScreen.ts, teammateNotice.ts
  screens/                  One component per screen (Welcome, Task, Correct, Revealed, Photo, Landmark, Finish, TimesUp, …)
  components/               Shared UI: GameHeader, ConfirmSheet, Toast, ConnectionBanner, Leaderboard, art.tsx
  lib/                      format.ts, storage.ts (localStorage), useNow.ts
  styles/                   questcity.css (design system), quest-screens.css, app.css
frontend-mocks/             Static HTML mockups of every screen (reference for UI work, not runtime code)
backend/                    Python 3.12 + FastAPI + SQLAlchemy
backend/questtour/
  main.py                   create_app factory (injects settings, session_factory, blob_store, clock)
  api/                      FastAPI routers: play.py (player API), images.py, schemas.py, deps.py
  services/                 Business logic: game.py, state.py, access.py, leaderboard.py, photos.py
  sync/                     YAML config loader + sync/apply (landmarks.yaml, games.yaml, teams.yaml)
  cli/sync_config.py        `sync-config` CLI (validate → upsert → issue tokens → print links)
  models.py db.py           SQLAlchemy models / engine; alembic/ holds migrations
  clock.py tokens.py normalize.py safenames.py imagetypes.py storage.py settings.py
backend/config/             Sample config: landmarks.yaml, games.yaml, teams.yaml, images/
backend/tests/              pytest suite; factories.py has seed_game()
docker-compose.yml          PostgreSQL 16 + Azurite for local dev
```

## Commands

Backend (from `backend/`, uses [uv](https://docs.astral.sh/uv/)):

```bash
uv sync                              # install deps (uv sync --python 3.13 if no 3.12 interpreter)
uv run pytest -q                     # tests (SQLite by default)
uv run ruff check .                  # lint (line-length 100)
TEST_DATABASE_URL=postgresql+psycopg://questtour:questtour@localhost:5432/questtour \
  uv run pytest -q                   # adds the postgres-marked tests
```

Frontend (from `frontend/`):

```bash
npm install
npm run dev          # dev server on :5173, proxies /api to :8000 (override with DEV_API_TARGET)
npm test             # vitest run
npm run typecheck    # tsc -b
npm run build        # tsc -b && vite build → frontend/dist
```

Full local dev: `docker compose up -d` at repo root, then follow README.md ("Docker dev path").
No-Docker fallback (SQLite + local file storage) is also in the README. Frontend tests and backend
tests must both pass before considering any change done.

## The specs are the contract

`specs/requirements.md` defines numbered rules **R-1 … R-23**; `specs/technical.md` the architecture;
`specs/frontend-design-brief.md` the UI. Code comments, tests and UI copy reference these rule IDs —
keep that linkage. When behaviour and code disagree, the spec wins; when you change behaviour, update
the spec in the same change.

Non-negotiable invariants (violating these is a bug even if tests pass):

- **The server is the source of truth.** Clock, answer checking, penalties, timeouts and game flow
  are computed server-side; the browser only displays. Never add game logic to the frontend.
- **Accepted answers never leave the server.** Answer checking (R-9) happens in
  `questtour/normalize.py` + services; the answer payload is never included in any API response.
- **Access tokens (R-21).** Tokens are ≥128 bits, URL-safe. The DB stores only a hash; the plaintext
  lives only in `teams.yaml`. `sync-config` prints/rewrites them.
- **Concurrency (R-18).** Answer/hint/reveal/photo actions take a DB lock on the game run row inside
  one transaction ("first correct answer wins", each penalty charged exactly once). Teammates sync by
  polling every 60 s (plus after own actions and on visibility change) — no WebSockets in v1.
- **One run per assignment (R-13).** A game can never be replayed; reopened links show the finish
  state again — except service (test) links (R-25), which can be reset from the game screen.
- **Photos (R-10).** Stored at original resolution, never re-encoded, max 20 MB, JPEG/PNG/HEIC/WebP.
  Players never see photos, not even thumbnails. Path:
  `photos/{Game}/{Team}/{timestamp}_{position}_{landmark}.{ext}` (game time zone, safe names via
  `safenames.py`, `_2`/`_3` suffix on collision).
- **404 handling.** The SPA is served only for known routes; everything else returns a real HTTP 404
  (see `questtour/web.py`).
- **Multi-host readiness (R-20).** Every config table carries `host_id`; v1 uses one value. Don't
  remove it. Same for CMS-friendliness: the DB is the runtime source of data; YAML is only the input.
- **Python 3.12 compatibility.** `pyproject.toml` requires ≥3.12 and production runs 3.12 — do not
  use 3.13+-only stdlib features.

## Backend conventions

- Layering: `api/` (HTTP + Pydantic schemas) → `services/` (game logic, all invariants) → `models.py`
  / `db.py` / `storage.py`. Keep business rules out of routers.
- `clock.py` provides the clock; everything that needs "now" takes it as a dependency (injected via
  `create_app`) so tests can drive time with the `FakeClock` fixture from `tests/conftest.py`.
- Tests use SQLite in-memory by default (`StaticPool`); `tests/test_concurrency_pg.py` and other
  `postgres`-marked tests need `TEST_DATABASE_URL`. Seed data via `tests/factories.seed_game`.
- YAML config timestamps must be quoted ISO-8601 strings; without an offset they are read in the
  game's time zone. `sync/schema.py` uses pydantic `ConfigDict(coerce_numbers_to_str=...)`.
- All settings come from environment variables (`.env` locally, see `.env.example`; App Service app
  settings in Azure). No hard-coded config values.
- Secrets: `backend/.env` is git-ignored. **`backend/config/teams.yaml` holds live game links after a
  `sync-config` run — commit it only in this private repo, and never copy tokens into code, tests or
  logs.**

## Frontend conventions

- Screens live in `src/screens/` and are dumb-ish; routing between them is a pure function:
  `game/selectScreen.ts` maps `GameState` + local UI flags → screen. Keep it pure and tested.
- `game/useGame.ts` owns the state machine: polling, offline handling, teammate toasts ("stale" /
  "already_started" / "game_over" outcomes from other phones), and the `act()` wrapper for actions.
  Photo upload goes through `track()` so in-flight uploads don't trigger teammate toasts.
- Types mirror the backend API contract in `src/api/types.ts`; keep them in sync when changing
  `backend/questtour/api/schemas.py`.
- Styling: the design system is `src/styles/questcity.css` (component classes `qc-*`, prefix of the
  mocks in `frontend-mocks/`) on top of tokens from `frontend-mocks/ds/questcity/tokens.json` — warm
  limestone surface, patina-green primary (`accent`), gold for penalties/warnings, theatre-red for
  errors. Every value must read a CSS token, never a raw colour/size. Screen layout classes are `qs-*`
  (`quest-screens.css`).
- Design at 390 × 844 first, verify nothing breaks at 360 × 740. Portrait only, mobile-first. Every
  interactive element gets the 3px focus ring. Font is Atkinson Hyperlegible + Fraunces display.
- When implementing or changing a screen, compare against the corresponding
  `frontend-mocks/<Screen>.dc.html` (open it in a browser) and the design brief §5 mapping.
- Accessibility/tone: penalties are always shown *before* they are paid (confirmation sheets show the
  cost, e.g. "+10 min" in gold).

## Testing expectations

- New backend behaviour → a pytest in `backend/tests/` covering the rule (many tests are named after
  the feature: `test_normalize.py`, `test_safenames.py`, `test_game_flow.py`, …). Drive time with the
  `clock` fixture (`clock.advance(minutes=…)`) — never `datetime.now()` in services.
- New frontend behaviour → vitest colocated with the source (`*.test.ts(x)`); use
  `src/test/fixtures.ts` for game-state fixtures and `src/test/setup.ts` for jsdom setup.
- Screens have per-screen test files (e.g. `TaskScreen.test.tsx`, `WelcomeScreen.test.tsx`) covering
  the mock-up states listed in `frontend-mocks/README.md` (wrong answer, hints, reveal unlocked,
  time warning, offline banner, teammate toast, …).

## Gotchas

- Game rule edits (`max_duration_minutes`, reveal N/X/P, validity windows) **apply live to running
  games** — only the landmark order of a running game is frozen (a run keeps the task list it started
  with). Be careful when "just changing" config handling.
- Team names are unique; swapping two names requires a temporary name in two `sync-config` runs.
- `accepted_answers[0]` is the answer shown on reveal — order matters.
- Azurite/`docker compose` notes: the compose file's flags (`--location`, `--skipApiVersionCheck`)
  exist for a reason; blobs survive `down/up`.
- The Vite proxy only forwards `/api`; game links printed by `sync-config` point at
  `PUBLIC_BASE_URL` (default `http://localhost:5173` in dev).

## Git / PRs

- Commits and PR descriptions follow the repo's existing style (concise, imperative).
- CI expectation: backend pytest + ruff, frontend vitest + typecheck must pass on every PR.
