# Happy Post Frontend

Next.js frontend MVP for Happy Post. It renders a small post board that lists and creates posts through the existing FastAPI API.

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

The browser calls relative `/api/posts` paths. For local development, `next.config.ts` rewrites those paths to `BACKEND_BASE_URL`, which defaults to `http://localhost:8000`. Copy `.env.example` to `.env.local` only when a different local backend URL is needed.

In deployment, the ALB routes `/api/*` directly to FastAPI and `/*` to this frontend service. No browser CORS configuration, AWS credential, or database credential belongs in the frontend.

## Container run

From the repository root, run the local two-service stack:

```bash
docker compose up --build -d
docker compose ps
docker compose down --remove-orphans
```

The frontend binds only to `http://127.0.0.1:3000`. It preserves browser-relative
`/api/posts` requests and proxies them across the Compose network to
`http://backend:8000`. The backend host binding defaults to `127.0.0.1:8000`; if
that port is temporarily unavailable, use the non-sensitive
`HAPPY_POST_BACKEND_HOST_PORT=18000` with the Compose commands. This changes only
the host-side backend port, not internal routing. Compose has no PostgreSQL service;
the frontend image runs as a non-root user and includes no secrets. P3 does not
deploy or change AWS, ECS, ALB, OIDC, or Aurora.

## Routes

| Path | Purpose |
| --- | --- |
| `/` | Create and list Happy Posts |
| `/healthz` | Container-local health response with version; used by the Compose health check |
| `/version` | Container-local version response |
| `/frontend/healthz` | Public frontend health alias for the planned ALB route |
| `/frontend/version` | Public frontend version alias for the planned ALB route |
