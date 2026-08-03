# Happy Post Backend

FastAPI backend MVP for Happy Post. It provides health and version routes, simple email/password MVP authentication, and a PostgreSQL-backed daily-entry API for recording at least three small happy things before sleep, with support for additional happy items. Production uses `DATABASE_URL` injected from Secrets Manager; local tests can run without AWS secrets. The schema stores users separately from entries: one `daily_entries` row per user and date, plus one `daily_entry_items` row per happy item.

## Local setup

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
cd backend
uv sync --group dev
uv run --group dev pytest
uv run --group dev ruff check .
uv run --group dev fastapi dev app/main.py
```

Copy `.env.example` to `.env` only for local use. Keep credentials out of source control. `DATABASE_URL` enables SQLAlchemy persistence; without it, tests and local dev use in-memory repositories. Auth sessions use opaque random cookie tokens; only SHA-256 token hashes are stored in PostgreSQL. `SESSION_TTL_SECONDS` controls the session lifetime.

## Container run

From the repository root, start the local PostgreSQL-backed stack with:

```bash
docker compose up --build -d
docker compose ps
docker compose down --remove-orphans
```

The backend binds to `http://127.0.0.1:8000` by default and serves `/healthz`.
If that host port is occupied, use the non-sensitive temporary override
`HAPPY_POST_BACKEND_HOST_PORT=18000` with each Compose command; the container
still listens on port 8000. Compose also starts local PostgreSQL on loopback
port 5432 by default; use `HAPPY_POST_DB_HOST_PORT=15432` when that host port is
occupied. The `backend-migrate` one-shot service runs `alembic upgrade head`
before the backend starts. The frontend reaches this backend internally as
`http://backend:8000` and proxies relative `/api/auth/*` and `/api/entries/*`
requests there. The
runtime image runs as a non-root user and contains no AWS secrets.

## Routes

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/healthz`, `/backend/healthz` | Health response with version |
| `GET` | `/version`, `/backend/version` | Version response |
| `POST` | `/api/auth/signup` | Create a user with email/password and set the HttpOnly session cookie |
| `POST` | `/api/auth/signin` | Verify email/password and set the HttpOnly session cookie |
| `POST` | `/api/auth/signout` | Clear the session cookie |
| `GET` | `/api/auth/me` | Return the signed-in user profile |
| `GET` | `/api/entries/today` | Retrieve today's happy-items daily entry |
| `PUT` | `/api/entries/today` | Create or update today's entry |
| `GET` | `/api/entries?month=YYYY-MM` | List saved entries for a month, newest first |
| `GET` | `/api/entries/{entry_date}` | Retrieve one entry by `YYYY-MM-DD` |

All `/api/entries/*` routes require a signed-in user and can read or write only that user's records. Run `uv run --group dev alembic history` to inspect the migration history without connecting to a database. Run `DATABASE_URL=<local-url> uv run --group dev alembic upgrade head` to apply the append-only `0001_create_posts` then `0002_create_users_daily_entries` chain. The `0002` migration replaces the temporary `posts` table with `users`, `user_sessions`, `daily_entries`, and `daily_entry_items`.
