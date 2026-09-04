# Finance Staging Evidence: 2026-09-04

## Scope

Production-shaped staging validation for the Foundation-provided Postgres/Auth
stack and Finance release `8f34207`.

Environment:

- Subscription: staging subscription recorded in the deployment change record
- Resource group: `rg-afin-ai-platform-staging`
- Runtime: `vm-afin-ai-runtime-stg`
- Ingress: `vm-afin-ai-ingress-stg`
- Foundation recovery change: `9c99030`
- Finance smoke-test change: `5be94ec`

No production data, credentials, bearer tokens, or secret values are included in
this record.

## Results

The checked-in `scripts/staging/finance-smoke-test.sh` passed after the runtime
VM and ingress VM were started:

```text
stage=inputs.pass
stage=auth.pass
stage=enqueue http=202
stage=worker-restarted
stage=worker-recovery.pass status=succeeded
stage=replay http=202
stage=idempotency.pass same_job_id=true
stage=unauthenticated-rejection http=401
stage=unauthenticated-rejection.pass http=401
stage=audit.pass entries=25
{"event":"finance_staging_smoke.pass","async_status":"succeeded","idempotency":"same_job_id","worker_restart":"recovered","unauthenticated_status":401}
```

The audit count is cumulative and is not an event count for this run.

## Recovery Evidence

- Docker recovered after VM startup through `platform-compose-start.service`.
- Foundation services became healthy.
- Finance API and worker were restored after the persistent Finance release
  environment was installed.
- The Finance permission bootstrap preserved `finance.research.create`.
- The worker restart completed the queued research successfully.

## Release Decision

This evidence satisfies the Finance staging functional and restart-recovery
checks. It does not by itself authorize production promotion. Production still
requires the applicable readiness checklist, exact production image/configuration
validation, backup/restore evidence, alert verification, named ownership, and an
approved change record.
