# Happy Post Frontend

Next.js frontend MVP for Happy Post. It renders a warm sign-in/sign-up flow and bedtime page that asks the signed-in user to record at least three small happy things, save them through the FastAPI API, and revisit their own saved days in a simple monthly history calendar.

## Local setup

Requires Node.js 20.9+ and a locally running backend at `http://localhost:8000`.

```bash
cd frontend
npm install
npm test -- --run
npm run lint
npm run build
npm run dev
```

The browser calls relative `/api/auth/*` and `/api/entries/*` paths. For local development, `next.config.ts` rewrites those paths to `BACKEND_BASE_URL`, which defaults to `http://localhost:8000`. Copy `.env.example` to `.env.local` only when a different local backend URL is needed.

In deployment, the ALB routes `/api/*` directly to FastAPI and `/*` to this frontend service. No browser CORS configuration, AWS credential, or database credential belongs in the frontend.

## Container run

From the repository root, run the local PostgreSQL-backed stack:

```bash
docker compose up --build -d
docker compose ps
docker compose down --remove-orphans
```

The frontend binds only to `http://127.0.0.1:3000`. It preserves browser-relative
`/api/auth/*` and `/api/entries/*` requests and proxies them across the Compose network to
`http://backend:8000`. The backend host binding defaults to `127.0.0.1:8000`; if
that port is temporarily unavailable, use the non-sensitive
`HAPPY_POST_BACKEND_HOST_PORT=18000` with the Compose commands. Local PostgreSQL
binds to `127.0.0.1:5432` by default and can be moved with
`HAPPY_POST_DB_HOST_PORT=15432`. These overrides change only host-side ports, not
internal routing. The frontend image runs as a non-root user and includes no
secrets.

## Routes

| Path | Purpose |
| --- | --- |
| `/` | Sign in or sign up, then record and revisit at least three small happy things |
| `/healthz` | Container-local health response with version; used by the Compose health check |
| `/version` | Container-local version response |
| `/frontend/healthz` | Public frontend health alias for the planned ALB route |
| `/frontend/version` | Public frontend version alias for the planned ALB route |
