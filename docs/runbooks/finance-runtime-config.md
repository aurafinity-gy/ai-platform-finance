# Finance Runtime Configuration

This runbook documents the environment required by the Finance API runtime.
It applies to `services/api-fastapi` and any deployed composition root that
builds the runtime without injected test doubles.

## Required Environment Variables

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
