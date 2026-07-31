# Happy Post Frontend

Next.js frontend MVP for the Happy Post assessment. It renders a small post board that lists and creates posts through the existing FastAPI API.

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

## Routes

| Path | Purpose |
| --- | --- |
| `/` | Create and list Happy Posts |
| `/healthz`, `/frontend/healthz` | Health response with version |
| `/version`, `/frontend/version` | Version response |
