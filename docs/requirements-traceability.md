# Requirements Traceability

| Requirement | Baseline decision | Evidence location |
| --- | --- | --- |
| Frontend and backend application delivery | Next.js frontend and FastAPI backend are separate services; both MVPs are implemented locally | [Architecture](architecture.md), [Backend MVP](../backend/README.md), [Frontend MVP](../frontend/README.md) |
| Health and version endpoints | Backend has `/healthz` and `/version`; frontend has container-local `/healthz` and `/version` plus public `/frontend/*` aliases | [Backend MVP](../backend/README.md), [Frontend MVP](../frontend/README.md), [`frontend/app/healthz/route.ts`](../frontend/app/healthz/route.ts), [`frontend/app/version/route.ts`](../frontend/app/version/route.ts) |
| Containerisation | Separate non-root FastAPI and Next.js images are implemented; Compose defines only `backend` and `frontend`, loopback host bindings, health checks, and internal `backend:8000` routing | [`backend/Dockerfile`](../backend/Dockerfile), [`frontend/Dockerfile`](../frontend/Dockerfile), [`compose.yaml`](../compose.yaml), [Local containers validation](local-containers-validation.md) |
| Automated tests and checks | Backend tests/linting and frontend checks are implemented locally; CI delivery is pending | [Backend MVP](../backend/README.md), [Frontend MVP](../frontend/README.md), [Implementation backlog](implementation-backlog.md) |
| Image scanning and registry | The platform root defines one private immutable, scan-on-push ECR repository per workload; a later delivery workflow publishes and selects immutable image digests | [Architecture](architecture.md), [Security decisions](security-decisions.md) |
| ECS delivery | One cluster hosts two Fargate services behind an ALB | [Architecture](architecture.md) |
| Public domain and TLS | Cloudflare delegates the application subdomain to Route 53; HTTPS ends at ALB | [Architecture](architecture.md) |
| Persistent application data | Deployed private RDS PostgreSQL is reachable only from the backend service | [Architecture](architecture.md), [Security decisions](security-decisions.md) |
| Database recovery | RDS automated backups and point-in-time recovery are configured for one day in sandbox, the active Free Plan maximum replacing the seven-day target; a future paid environment restores the longer objective | [Operations](operations.md) |
| Infrastructure as code | Terraform manages foundation and steady-state resources after bootstrap | [Architecture](architecture.md) |
| Controlled deployment | One GitHub environment, `sandbox`, provides deployment role and configuration separation without required reviewers | [Security decisions](security-decisions.md) |
| Rollback | Immutable image digests and ECS revision rollback are required | [Deployment and rollback](deployment-and-rollback.md) |
| Least privilege | OIDC trust, separate operational roles, and narrow runtime permissions | [Security decisions](security-decisions.md) |
| End-to-end TLS | Deferred optional enhancement, not baseline | [Architecture](architecture.md) |

This table records the approved design, completed application MVPs, local P3 containerisation, applied Terraform network and RDS data foundations, and CI controls. Application database integration remains pending an approved workload implementation.
