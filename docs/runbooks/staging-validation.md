# Finance Staging Validation

The Finance staging smoke test is an operational acceptance check for the
foundation-provided Postgres/Auth deployment and the Finance API/worker.

## Prerequisites

- Run on the staging runtime VM as a privileged operator.
- Foundation Auth, Postgres, Finance API, and Finance worker containers are running.
- `/run/m5-provider-admission/password` exists for the synthetic operator.
- `/srv/platform/runtime-secrets/supabase-anon-key` exists.
- The synthetic operator has `finance.research.create` for the staging tenant.

## Run

Run the checked-in `scripts/staging/finance-smoke-test.sh` through the staging
VM Run Command mechanism, or execute it directly on the runtime VM after the
release has installed it:

```sh
sh scripts/staging/finance-smoke-test.sh
```

The script creates its own temporary request state and dynamically resolves the
current Finance API container address. It must not be split across separate
Run Command executions.

## Checks

The script verifies:

- Synthetic input files are present.
- Authenticated operator login succeeds.
- Finance job enqueue returns HTTP 202.
- The worker recovers after a restart and completes the job.
- Replaying the request returns HTTP 202 and the same `job_id`.
- An unauthenticated job lookup returns HTTP 401.
- A Finance research audit entry is persisted.

## Expected result

```text
{"event":"finance_staging_smoke.pass","async_status":"succeeded","idempotency":"same_job_id","worker_restart":"recovered","unauthenticated_status":401}
```

The audit count is cumulative and may be greater than one. The test never prints
passwords, anon keys, bearer tokens, or response bodies containing credentials.

## Recovery notes

If the VM has restarted, run the foundation synthetic identity bootstrap before
the smoke test. The bootstrap must be followed by the Finance permission grant
unless the deployment automation applies that grant. Do not hard-code Docker
container IP addresses; they change when containers are recreated.

## Release gate

The smoke test is necessary but not sufficient for production release. A release
also requires successful deployment validation, migration verification, rollback
readiness, monitoring/alert checks, and an approved production change record.
