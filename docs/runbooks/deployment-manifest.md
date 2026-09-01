# Finance Deployment Manifest

Use `compose.release.yaml` as the production-shaped application deployment
manifest for Finance when you deploy the repo services through Docker Compose
or a compatible orchestration flow.

## Purpose

The manifest runs the Finance API and Finance worker as immutable release
artifacts. It assumes the database and authentication services are provided by
the target environment.

## Required Release Variables

- `FINANCE_IMAGE_REGISTRY`
- `FINANCE_RELEASE_VERSION`
- `FINANCE_API_BIND_ADDRESS`
- `FINANCE_DATABASE_URL`
- `FINANCE_AUTH_JWKS_URL`
- `FINANCE_AUTH_ISSUER`
- Optional `FINANCE_AUTH_AUDIENCE`
- `FINANCE_WORKER_ACTOR_ID`
- `FINANCE_WORKER_TENANT_ID`

## Services

- `finance-api`
  - Exposes the HTTP API on port `8011`.
  - Uses `/livez` for health checks.
  - Resolves auth and database settings from the release environment.

- `finance-worker`
  - Runs the Finance background worker for research workflows.
  - Uses the same release version and database, with a provisioned service
    actor and tenant scope.

## Usage

```powershell
docker compose --env-file <release.env> -f compose.release.yaml config
docker compose --env-file <release.env> -f compose.release.yaml up -d
```

## Operational Notes

- Keep the release environment file outside source control.
- Use immutable image tags or digests for `FINANCE_RELEASE_VERSION`.
- Verify the deployed artifact against the staging validation and post-release
  runbooks.

## Related Files

- [`compose.release.yaml`](../../compose.release.yaml)
- [`docs/runbooks/release-operations.md`](release-operations.md)
- [`docs/runbooks/staging-validation.md`](staging-validation.md)
- [`docs/runbooks/post-release.md`](post-release.md)
