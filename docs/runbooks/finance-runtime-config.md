# Finance Runtime Configuration

This runbook documents the environment required by the Finance API runtime.
It applies to `services/api-fastapi` and any deployed composition root that
builds the runtime without injected test doubles. The worker has separate
identity settings described below.

## Required Environment Variables

- `FINANCE_API_BIND_ADDRESS`
  - Host bind address for the API deployment, such as `0.0.0.0` or a private
    interface address.

- `FINANCE_DATABASE_URL`
  - Postgres connection string for the Finance unit of work.
  - Example: `postgresql://platform_api:secret@localhost:5432/postgres`

- `FINANCE_AUTH_JWKS_URL`
  - HTTPS URL for the JSON Web Key Set used to verify bearer tokens.

- `FINANCE_AUTH_ISSUER`
  - Expected `iss` claim in bearer tokens.

## Optional Environment Variables

- `FINANCE_AUTH_AUDIENCE`
  - Expected `aud` claim.
  - Defaults to `authenticated` when omitted.

## Worker Environment Variables

The executable worker requires the same `FINANCE_DATABASE_URL` plus:

- `FINANCE_WORKER_ACTOR_ID`
  - UUID of a provisioned service actor with the required Finance permission.
- `FINANCE_WORKER_TENANT_ID`
  - UUID of the tenant scope the worker is authorized to process.

The worker identity must have the `finance.research.worker` permission in that
tenant. It should not be granted broad human or live-trading permissions.

The worker no longer starts with an in-memory database or synthetic membership
grant. Create the service membership through the approved platform migration or
administration workflow before deployment.

## Runtime Behavior

- The service resolves authenticated actor identity from a bearer token.
- The service resolves tenant scope from the incoming request context.
- The runtime opens a Postgres-backed finance unit of work per request.
- The request lifecycle stores idempotency and audit entries in the database.

## Local Validation

When you run the executable composition root directly, make sure the
environment is populated before starting the service. From the
`services/api-fastapi` directory:

```powershell
$env:FINANCE_DATABASE_URL = "postgresql://platform_api:secret@localhost:5432/postgres"
$env:FINANCE_AUTH_JWKS_URL = "https://auth.example.local/.well-known/jwks.json"
$env:FINANCE_AUTH_ISSUER = "https://auth.example.local"
$env:FINANCE_AUTH_AUDIENCE = "authenticated"
uv run finance-api
```

## Related Files

- [`docs/decisions/0003-finance-runtime-uses-postgres-and-jwt-context.md`](../decisions/0003-finance-runtime-uses-postgres-and-jwt-context.md)
- [`services/api-fastapi/src/finance_api_service/settings.py`](../../services/api-fastapi/src/finance_api_service/settings.py)
