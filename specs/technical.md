# Quest City Tour — Technical Specification

> Status: ready for review. Companion to [requirements.md](requirements.md).

## 1. Constraints

- Hosting on **Azure**, using Azure-native components for the web app, database, storage and roles.
- v1 is a browser-based website; there are no native apps.
- v1 has no admin UI; configuration comes from files (section 4).
- Expected scale for v1 is small: a few teams per day and at most about 10 game runs at the same time. The design must still allow multiple hosts and a CMS to be added later.

## 2. Architecture

```
Phone browser (React SPA)
        │  HTTPS / JSON
        ▼
Azure App Service (Linux)  ── Python FastAPI: REST API + serves the React build
        │                         │
        ▼                         ▼
Azure Database for         Azure Storage Account
PostgreSQL Flexible Server (Blob container "photos")
```

| Component | Azure service | Notes |
|---|---|---|
| Frontend | React SPA (TypeScript, Vite), built and served as static files by the backend | Mobile-first |
| Backend | Python 3.12 + FastAPI on **Azure App Service** (Linux, B1 plan) | Single deployable unit; always on, no cold starts |
| Database | **Azure Database for PostgreSQL Flexible Server** (Burstable B1ms) | Configuration and runtime state |
| Photos | **Azure Storage Account**, Blob container `photos` | Original files; the host browses them with Azure Storage Explorer or the Portal |
| Identity | **Managed identity** for App Service → PostgreSQL and Blob; **Entra ID + Azure RBAC** for people | No secrets in code |
| Secrets | App Service settings or Key Vault references | |

Estimated cost: about €25–40/month (to be confirmed in the Azure pricing calculator).

## 3. Key design decisions

- **Server is the source of truth.** Game state, the clock (R-2, R-8), answer checking (R-9) and penalties are all calculated on the server. The browser only displays them.
- **Concurrency.** Answer, hint, reveal and photo actions run in a database transaction that locks the game run row. This guarantees "first correct answer wins" and "each penalty charged once" (R-18).
- **Team sync by polling.** Each phone fetches the game run state every **60 seconds**, and also immediately after its own action and when the page becomes visible again (R-18). No real-time service (SignalR/WebSockets) is needed in v1.
- **Session persistence.** The access token in the URL identifies the assignment, and the browser stores the token and an anonymous device ID in `localStorage`. Reopening the page reloads the state from the server (R-17).
- **Access tokens.** At least 128 bits of randomness, URL-safe; only a hash is stored in the database. Requests outside the validity window or with a reissued token get a friendly "Link not valid" page (R-21).
- **Accepted answers are never sent to the client.**
- **Time limits are enforced on the server.** The maximum duration and validity window (R-8) are checked on every request, so the game ends correctly even if no phone is open.
- **Multi-host readiness.** Every configuration table has a `host_id` column (R-20); v1 uses a single value.

## 4. Configuration

- Configuration lives as YAML files in the repo under `config/`: `landmarks.yaml`, `games.yaml`, `teams.yaml` (teams plus team↔game assignments with validity window and exit message). Landmark pictures go under `config/images/`.
- A command-line script `sync-config`:
  1. validates the files (unique IDs, landmark references exist, Hint 2 only with Hint 1, at least one accepted answer, unique team names, valid time zone, etc.);
  2. upserts them into PostgreSQL and uploads the pictures to Blob storage;
  3. generates missing access tokens and prints each team's game link;
  4. can reissue a token (`--reissue <team> <game>`).
- The admin runs it after changing configuration; no redeploy is needed. At runtime the database is the only source of data, so a future CMS edits the database directly.
- A configuration change must not alter game runs that are already in progress. Each run keeps the task list it started with.

## 5. Photo storage

- Container `photos`, path `{GameName}/{TeamName}/{yyyy-MM-dd_HH-mm-ss}_{TaskNo}_{LandmarkName}.{ext}` (R-10), using the game's time zone. Folder and file names are built from the names at upload time.
- Upload goes through the backend, which checks the size (20 MB max) and the file type (JPEG, PNG, HEIC, WebP) and writes the blob. The original is never re-encoded.
- The container is private; no public access. Hosts get read/delete access through Azure RBAC (role *Storage Blob Data Contributor*).

## 6. Roles

| Role | Who | Access |
|---|---|---|
| Player | Anyone with a valid game link | Player API for that assignment only |
| Host | Host staff (Entra ID users) | Read/delete photos in Blob storage |
| Admin | Operator (Entra ID users) | Runs `sync-config`; manages Azure resources |

## 7. Deployment and operations

| Topic | Decision |
|---|---|
| Environments | `dev`: local, with PostgreSQL in Docker and the Azurite storage emulator. `prod`: Azure. No staging environment in v1. |
| Infrastructure as code | **Terraform** (azurerm provider) in `infra/`. State is kept remotely in a separate Azure Storage container. All resources in section 2 are defined there. |
| CI/CD | **GitHub Actions**. Pull requests run lint and tests (backend: pytest; frontend: unit tests); merging to `main` builds and deploys to prod. |
| Monitoring | None in v1, beyond the standard App Service logs. |
| Backups | PostgreSQL built-in backups with 7-day retention. Soft delete on the `photos` container with 14-day retention. |
| Budget | Azure budget alert at **€45/month**. |
