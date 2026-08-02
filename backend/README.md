# Happy Post Backend

FastAPI backend MVP for Happy Post. It provides health and version routes plus a minimal in-memory Posts API. PostgreSQL schema metadata and an Alembic migration are included for later private RDS integration; this MVP does not connect to or create a database.

## Local setup

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
cd backend
uv sync --group dev
uv run --group dev pytest
uv run --group dev ruff check .
uv run --group dev fastapi dev app/main.py
```

Copy `.env.example` to `.env` only for local use. Keep credentials out of source control. `DATABASE_URL` is optional in this phase.

## Container run

From the repository root, start the two-service local stack with:

```bash
docker compose up --build -d
docker compose ps
docker compose down --remove-orphans
```

The backend binds to `http://127.0.0.1:8000` by default and serves `/healthz`.
If that host port is occupied, use the non-sensitive temporary override
`HAPPY_POST_BACKEND_HOST_PORT=18000` with each Compose command; the container
still listens on port 8000. Compose contains no PostgreSQL service. The frontend
continues to reach this backend internally as `http://backend:8000` and proxies
its relative `/api/posts` requests there. The runtime image runs as a non-root
user and contains no secrets. This is local-only P3 work, not RDS or AWS deployment.

## Routes

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/healthz`, `/backend/healthz` | Health response with version |
| `GET` | `/version`, `/backend/version` | Version response |
| `POST` | `/api/posts` | Create `{ "message": "Hello" }` |
| `GET` | `/api/posts` | List posts newest first |
| `GET` | `/api/posts/{id}` | Retrieve one post |

Run `uv run --group dev alembic history` to inspect the initial schema revision without connecting to a database.
