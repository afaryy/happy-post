# Happy Post Backend

FastAPI backend MVP for the Happy Post assessment. It provides health and version routes plus a minimal in-memory Posts API. PostgreSQL schema metadata and an Alembic migration are included for later private RDS integration; this MVP does not connect to or create a database.

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

## Routes

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/healthz`, `/backend/healthz` | Health response with version |
| `GET` | `/version`, `/backend/version` | Version response |
| `POST` | `/api/posts` | Create `{ "message": "Hello" }` |
| `GET` | `/api/posts` | List posts newest first |
| `GET` | `/api/posts/{id}` | Retrieve one post |

Run `uv run --group dev alembic history` to inspect the initial schema revision without connecting to a database.
