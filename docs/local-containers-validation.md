# Local Containers Validation

This record covers P3 local containerisation only: two services (`backend` and
`frontend`) with no PostgreSQL or other infrastructure.

Compose explicitly tags its locally built images as `happy-post-backend:local`
and `happy-post-frontend:local`. This avoids Compose assigning implicit,
mutable `latest` tags during local development. The future ECR deployment
model remains unchanged: deployment task definitions must reference immutable
image digests, never mutable tags.

## Validation sequence and results

1. Build the backend image:
   `docker build --tag happy-post-backend:local backend` — passed.
2. Run the backend image temporarily, mapping its container port 8000 to an
   available loopback host port; run `docker exec happy-post-backend-check id -u`
   and request `/healthz` — passed: UID `999` (non-root) and HTTP `200`.
   Stop and remove the temporary container — passed.
3. Build the frontend image:
   `docker build --build-arg BACKEND_BASE_URL=http://backend:8000 --tag happy-post-frontend:local frontend`
   — passed.
4. Run the frontend image temporarily; run
   `docker exec happy-post-frontend-check id -u` and request `/healthz` —
   passed: UID `100` (non-root) and HTTP `200`. Stop and remove the temporary
   container — passed.
5. Run `docker compose config` with no environment override — passed. The
   default loopback publications are backend `8000` and frontend `3000`.
6. A separate EasyGo service temporarily owned host port 8000, so validation
   used `HAPPY_POST_BACKEND_HOST_PORT=18000 docker compose up --build -d`.
   This changes only the backend host port; container-to-container routing
   remains `backend:8000`.
7. Run `HAPPY_POST_BACKEND_HOST_PORT=18000 docker compose ps` — passed:
   exactly two healthy services, `backend` and `frontend`.
8. Request the backend health endpoint, frontend health endpoint, and
   frontend-proxied posts endpoint — passed: backend `/healthz` returned HTTP
   `200`, frontend `/healthz` returned HTTP `200`, and frontend `/api/posts`
   succeeded.
9. Run `HAPPY_POST_BACKEND_HOST_PORT=18000 docker compose down --remove-orphans`
   — passed; Compose cleanup completed successfully.

The alternate host-port setting was a validation-only workaround. Normal local
use continues to expose backend on loopback port 8000 and frontend on loopback
port 3000.
