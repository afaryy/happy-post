# Git, Commit, and Pull Request Conventions

## Branch Names

Use one of these prefixes:

```text
docs/<short-description>
feat/<short-description>
fix/<short-description>
chore/<short-description>
security/<short-description>
infra/<short-description>
ci/<short-description>
```

Examples:

```text
docs/add-assessment-baseline
feat/add-backend-health-api
infra/add-network-foundation
ci/add-trivy-gate
```

## Commit Messages

Use Conventional Commits:

```text
type(scope): concise imperative summary
```

Examples:

```text
docs: add assessment baseline documentation
feat(backend): add health and version endpoints
infra(network): add VPC foundation
ci: add frontend validation workflow
security: add Trivy image scanning gate
```

Rules:

- Make one logical change per commit.
- Use imperative, present-tense summaries.
- Keep the first line under 72 characters.
- Do not mix application, infrastructure, CI, and unrelated documentation in one commit.
- Add a body only for a non-obvious decision, risk, migration, or breaking change.
- Never commit secrets, generated credentials, Terraform state, or local environment files.

## Pull Requests

Use the same Conventional Commit format for the title:

```text
docs: add assessment baseline documentation
```

Use this description template:

```markdown
## Summary

- What changed
- Why it changed
- Relevant design decision or assessment requirement

## Scope

- Included:
- Explicitly excluded:

## Validation

- Commands run:
- Results:

## Security and infrastructure impact

- IAM / secrets / networking impact:
- Terraform or CloudFormation impact:
- Deployment or rollback impact:

## Risks and follow-up

- Known risks:
- Deferred work:
- Rollback approach:

## Checklist

- [ ] No secrets or Terraform state included
- [ ] Documentation updated
- [ ] Relevant tests, linting, and scans passed
- [ ] Infrastructure plan reviewed, if applicable
- [ ] Deployment is not included unless explicitly stated
```

## Local-first validation

Before creating a commit, validate the scoped change locally and fix any failures. At minimum, run the relevant tests, linting, formatting, and secret/dependency or image scans available for that component. For containerised services, also build the image locally and verify the documented health and version routes.

After local validation passes, review the diff for secrets and unintended files, commit the single logical change on a feature branch, push that branch, and open a pull request. GitHub then repeats the required checks. Do not commit or push directly to `main`, except for the initial empty-repository bootstrap described below.

## First Documentation Change

The initial documentation-only commit may be created and pushed directly to an otherwise empty `main` branch. Every later change follows the feature-branch and pull-request process above.

```text
Branch: docs/add-assessment-baseline
Commit: docs: add assessment baseline documentation
PR title: docs: add assessment baseline documentation
```
