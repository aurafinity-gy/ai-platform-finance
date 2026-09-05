# Finance Release Operations

This runbook turns the shared handbook release process into the Finance
deployment sequence. Use it alongside:

- [`ai-platform-handbook/volume-11-delivery-workflows/deployment-and-release-entry-point.md`](../../ai-platform-handbook/volume-11-delivery-workflows/deployment-and-release-entry-point.md)
- [`docs/runbooks/finance-runtime-config.md`](finance-runtime-config.md)
- [`docs/runbooks/local-finance-migration.md`](local-finance-migration.md)
- [`docs/runbooks/staging-validation.md`](staging-validation.md)
- [`docs/runbooks/production-readiness-checklist.md`](production-readiness-checklist.md)
- [`docs/runbooks/post-release.md`](post-release.md)
- [`docs/runbooks/deployment-manifest.md`](deployment-manifest.md)
- [`scripts/finance-smoke-test.ps1`](../../scripts/finance-smoke-test.ps1)
- Shared Foundation onboarding: [application-production-onboarding](https://github.com/aurafinity-gy/ai-platform-foundation/blob/main/docs/runbooks/application-production-onboarding.md)

## Release Inputs

- Release owner and rollback owner are named.
- The target environment is identified.
- The exact artifact digest or immutable image tag is known.
- The Finance production readiness checklist is complete or explicitly waived.
- The Finance runtime configuration has been prepared for the target
  environment.

## Deployment Order

1. Validate the release candidate in staging with the exact production image
   or digest using [`staging-validation.md`](staging-validation.md).
2. Apply any required database migrations using the documented additive
   migration order.
3. Deploy the Finance API runtime with the production configuration using
   [`deployment-manifest.md`](deployment-manifest.md).
4. Verify `/livez` and `/readyz` in the target environment.
5. Run the Finance smoke test against the deployed environment.
6. Confirm logs, metrics, traces, and audit events look healthy.
7. Promote the same artifact to the production environment when staging is
   stable and approved.
8. Verify the promotion with [`post-release.md`](post-release.md).

## Required Checks Before Promotion

- `uv sync --locked`
- `uv run ruff format --check .`
- `uv run ruff check .`
- `uv run pytest`
- `pwsh -File scripts/finance-smoke-test.ps1`
- Migration validation from [`local-finance-migration.md`](local-finance-migration.md)

## Runtime Expectations

- `FINANCE_DATABASE_URL`
- `FINANCE_AUTH_JWKS_URL`
- `FINANCE_AUTH_ISSUER`
- Optional `FINANCE_AUTH_AUDIENCE`
- Postgres-backed finance unit of work
- JWT-derived request context
- Tenant-scoped authorization and audit logging

## Rollback Guidance

- Keep the prior immutable artifact available until the release is verified.
- If a migration is forward-only, limit rollback to the application artifact and
  use a forward-fix for schema changes.
- If a release fails health checks, stop promotion and revert to the prior
  known-good artifact.

## Evidence To Record

- Deployment timestamp
- Artifact digest
- Staging validation result
- Production health check result
- Smoke test output
- Any rollback or forward-fix notes
