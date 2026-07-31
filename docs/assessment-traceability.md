# Assessment Traceability

| Assessment need | Baseline decision | Evidence location |
| --- | --- | --- |
| Frontend and backend application delivery | Next.js frontend and FastAPI backend are separate services | [Architecture](architecture.md) |
| Health and version endpoints | Component-scoped health and version routes are reserved | [Architecture](architecture.md) |
| Containerisation | Two independently built images are required | [Implementation backlog](implementation-backlog.md) |
| Automated tests and checks | Backend tests/linting and frontend checks precede delivery | [Implementation backlog](implementation-backlog.md) |
| Image scanning and registry | Each workload has a private ECR repository and image digest | [Security decisions](security-decisions.md) |
| ECS delivery | One cluster hosts two Fargate services behind an ALB | [Architecture](architecture.md) |
| Public domain and TLS | Cloudflare delegates the application subdomain to Route 53; HTTPS ends at ALB | [Architecture](architecture.md) |
| Persistent application data | Private RDS PostgreSQL is reachable only from the backend service | [Architecture](architecture.md), [Security decisions](security-decisions.md) |
| Database recovery | RDS automated backups and point-in-time recovery retain seven days of recovery points | [Operations](operations.md) |
| Infrastructure as code | Terraform manages foundation and steady-state resources after bootstrap | [Architecture](architecture.md) |
| Controlled deployment | One GitHub environment, `sandbox`, provides deployment role and configuration separation without required reviewers | [Security decisions](security-decisions.md) |
| Rollback | Immutable image digests and ECS revision rollback are required | [Deployment and rollback](deployment-and-rollback.md) |
| Least privilege | OIDC trust, separate operational roles, and narrow runtime permissions | [Security decisions](security-decisions.md) |
| End-to-end TLS | Deferred optional enhancement, not baseline | [Architecture](architecture.md) |

This table records design intent only. No application, Terraform, CI/CD, or AWS implementation has been added yet.
