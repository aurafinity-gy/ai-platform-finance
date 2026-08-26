# Finance Post-Release Verification

Use this runbook immediately after a Finance production promotion.

## First Ten Minutes

- Confirm the deployed artifact digest matches the reviewed release candidate.
- Confirm `/livez` is healthy.
- Confirm `/readyz` is healthy.
- Confirm logs, metrics, and traces are arriving in the production stack.
- Confirm no rollout alarms are firing.

## Functional Checks

- Run the Finance smoke test against the production target if the promotion
  procedure allows it.
- Verify that a representative finance workflow succeeds end to end.
- Verify that an invalid or unauthorized request is denied as expected.
- Verify that idempotent replay behavior still returns the prior result.

## Operational Checks

- Review error rate, latency, and dependency health for the release window.
- Confirm database connections and auth requests are healthy.
- Confirm audit entries are being recorded for accepted actions.
- Confirm no sensitive values are leaking in logs or traces.

## Escalation And Rollback

- If health checks fail, stop further promotion and revert to the prior known
  good artifact.
- If the database or auth layer regresses, follow the rollback or forward-fix
  plan documented in the release operations runbook.
- Record the incident or anomaly and link the release evidence.

## Evidence To Capture

- Promotion timestamp
- Artifact digest
- Smoke test result
- Health check status
- Any rollback or forward-fix action
- Any follow-up items for the next release

