# Finance Staging Validation

Use this runbook to validate a Finance release candidate in a staging or
production-shaped environment before promotion.

## Inputs

- The exact image digest or immutable release tag to be promoted.
- The target environment and namespace or deployment target.
- The release owner and rollback owner.
- The Finance production readiness checklist is complete or explicitly waived.

## Environment Checks

- Confirm the staging environment uses the Finance production runtime
  configuration.
- Confirm `FINANCE_API_BIND_ADDRESS` is set to the intended private or public
  interface for the staging topology.
- Confirm `FINANCE_DATABASE_URL`, `FINANCE_AUTH_JWKS_URL`, and
  `FINANCE_AUTH_ISSUER` are populated.
- Confirm any optional `FINANCE_AUTH_AUDIENCE` override matches the intended
  token policy.
- Confirm the deployment uses the same artifact that will be promoted to
  production.

## Database Validation

- Apply the additive Finance migrations in the documented order.
- Confirm `platform.memberships` exists.
- Confirm `platform.audit_entries` exists.
- Confirm `finance.research_records` exists.
- Confirm `finance.command_idempotency` exists.
- Confirm row-level security is enabled on Finance-owned tables.
- If asynchronous research is enabled, confirm `finance.research_jobs` exists
  and the worker-claim migration is applied before exercising claim, retry,
  and lease-expiry behavior.

## Runtime Validation

- Confirm `/livez` returns healthy.
- Confirm `/readyz` returns healthy with real database and auth dependencies.
- Confirm bearer-token verification rejects invalid issuer, audience, or
  signature values.
- Confirm tenant-scoped authorization works with the real membership data.
- Confirm the release path does not require demo headers or synthetic identity
  shortcuts.

## Functional Validation

- Run `pwsh -File scripts/finance-smoke-test.ps1` against the staging target.
- Exercise the representative finance workflow or API entrypoints used by the
  release.
- Verify idempotency replay behavior on a repeated request.
- Verify audit entries are written for accepted actions.

## Exit Criteria

- Health checks pass.
- Smoke test passes.
- Auth and tenant checks pass.
- No unexpected schema, logging, or rollout issues appear.
- The release is approved for promotion or explicitly stopped.

## Automated Run

With staging credentials and a staging bearer token available, run:

```powershell
pwsh -File scripts/finance-staging-validation.ps1 `
  -DatabaseUrl $env:FINANCE_DATABASE_URL `
  -ApiBaseUrl $env:FINANCE_STAGING_API_URL `
  -BearerToken $env:FINANCE_STAGING_BEARER_TOKEN `
  -TenantId $env:FINANCE_STAGING_TENANT_ID `
  -ApplyMigrations
```

Omit `-ApplyMigrations` when migrations are managed by the deployment
controller and only runtime validation is required.
