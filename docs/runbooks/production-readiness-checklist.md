# Finance Production Readiness Checklist

This checklist is the Finance-specific implementation of the shared release
process. The common lifecycle guidance should live in the handbook, especially
`ai-platform-handbook/volume-11-delivery-workflows` and
`ai-platform-handbook/volume-13-deployment-infrastructure`. Finance uses this
document to make that shared process concrete for the Finance bounded context.

Status: checklist, 2026-08-25

## 1. Change Scope And Ownership

- [ ] The release has a named owner and named rollback owner.
- [ ] The release scope is limited to Finance-owned code, migrations, docs, or
      configuration.
- [ ] Any cross-domain contract changes are explicitly documented and accepted.
- [ ] Any breaking change has an explicit migration or forward-fix plan.
- [ ] The change record, approval window, and communication channel are
      recorded.

## 2. Repository Health

- [ ] `main` is clean and matches `origin/main`.
- [ ] `uv sync --locked` succeeds.
- [ ] `uv run ruff format --check .` succeeds.
- [ ] `uv run ruff check .` succeeds.
- [ ] `uv run pytest` succeeds.
- [ ] Finance smoke test succeeds with `pwsh -File scripts/finance-smoke-test.ps1`.
- [ ] Any finance contract tests or consumer fixtures relevant to the release
      pass.

## 3. Runtime Configuration

- [ ] `FINANCE_DATABASE_URL` is defined for the target environment.
- [ ] `FINANCE_AUTH_JWKS_URL` is defined for the target environment.
- [ ] `FINANCE_AUTH_ISSUER` is defined for the target environment.
- [ ] `FINANCE_AUTH_AUDIENCE` is set or its default is accepted intentionally.
- [ ] Runtime secrets are stored in the approved secret store, not in source.
- [ ] The deployment manifest or environment file matches
      [`docs/runbooks/finance-runtime-config.md`](finance-runtime-config.md).
- [ ] The deployment manifest exists as
      [`compose.release.yaml`](../../compose.release.yaml) or an equivalent
      production-shaped overlay.

## 4. Database And Migrations

- [ ] All Finance migrations are additive and reviewed.
- [ ] The migration order is documented and tested in staging.
- [ ] `platform.memberships` exists in the target database.
- [ ] `platform.audit_entries` exists in the target database.
- [ ] `finance.research_records` exists in the target database.
- [ ] `finance.command_idempotency` exists in the target database.
- [ ] Row-level security is enabled on Finance-owned tables.
- [ ] The release has a rollback or forward-fix plan for database changes.
- [ ] A backup or restore point was taken before production migration.
- [ ] A restore drill has been executed or is explicitly approved as deferred.

## 5. Authentication And Authorization

- [ ] Bearer-token verification is enabled in the runtime.
- [ ] JWKS retrieval works against the production auth provider.
- [ ] Issuer, audience, signature, expiry, subject, and role checks pass.
- [ ] Request context resolves the actor and tenant from authenticated input.
- [ ] Finance permissions are enforced through membership lookups or RLS.
- [ ] Production roles are least-privilege and scoped to the Finance service.
- [ ] No production path trusts demo headers or synthetic identities.

## 6. Service Readiness

- [ ] `livez` returns healthy in the deployed environment.
- [ ] `readyz` returns healthy with the real database and auth dependencies.
- [ ] The service starts with the production configuration and image digest.
- [ ] Worker processes, if used, are deployed and healthy.
- [ ] If the worker is deployed, `FINANCE_WORKER_ACTOR_ID` and
      `FINANCE_WORKER_TENANT_ID` identify a provisioned least-privilege service
      membership.
- [ ] No local-only bootstrap path is required in production.
- [ ] The release image is immutable and referenced by digest or locked tag.

## 7. Observability And Operations

- [ ] Logs, metrics, and traces are routed to the production observability stack.
- [ ] Alerts exist for availability, error rate, latency, and dependency failure.
- [ ] A dashboard exists for release verification.
- [ ] Alert routing has been tested for the owning team.
- [ ] On-call or operational contacts are known for the release window.
- [ ] The release runbook documents the stop criteria and rollback trigger.

## 8. Safety And Data Integrity

- [ ] Finance idempotency is verified for the release path.
- [ ] Audit entries are produced for accepted workflow actions.
- [ ] Cross-tenant denial behavior has been exercised in staging.
- [ ] Sensitive values are not logged, echoed, or stored in plaintext.
- [ ] Backward compatibility is preserved for any consumers of Finance
      contracts.
- [ ] Any optional providers or integrations are intentionally enabled or kept
      disabled.

## 9. Staging And Canary Evidence

- [ ] The exact production image or digest passed staging validation.
- [ ] The exact production configuration passed staging validation.
- [ ] The finance smoke test passed in an environment matching production
      topology.
- [ ] The release was exercised with representative requests and expected
      denials.
- [ ] Any canary window met its success criteria.
- [ ] Any canary stop criteria were documented and reviewed.
- [ ] [`docs/runbooks/release-operations.md`](release-operations.md) was used to
      guide the release sequence.
- [ ] [`docs/runbooks/staging-validation.md`](staging-validation.md) passed for
      the exact release candidate.

## 10. Go/No-Go

- [ ] All checklist items above are complete or explicitly waived by the named
      approver.
- [ ] The release can be rolled back without ambiguity.
- [ ] The team agrees the system is ready for the intended production exposure
      level.
- [ ] [`docs/runbooks/post-release.md`](post-release.md) is ready for the
      promotion window.
