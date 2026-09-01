# Finance MVP Application Acceptance

Use this runbook before promoting the first Finance application slice beyond
staging.

## Scope

The MVP proves authenticated, tenant-scoped Finance research intake and
asynchronous processing. It is not a live trading system and must not place
orders or connect to production broker credentials.

## Acceptance Checks

- Open the public application at `https://app.<environment-domain>/`.
- Confirm the Foundation web surface responds over HTTPS.
- Sign in using the environment's approved test operator.
- Confirm the session is associated with the expected tenant.
- Submit one bounded Finance research request.
- Confirm the request receives a queued job response.
- Confirm the worker completes the job and a result is visible.
- Repeat the request with the same idempotency key and confirm replay behavior.
- Confirm a different tenant cannot read or mutate the request.
- Confirm an invalid or expired token is rejected.
- Confirm the action produces an audit entry.
- Confirm `/livez` and `/readyz` remain healthy after the workflow.

## Evidence

Record the following without storing tokens, passwords, or personal data:

- application release identifier;
- Finance image release identifier;
- test tenant identifier;
- correlation identifiers;
- job status and result status;
- idempotency replay result;
- authorization and audit outcomes;
- operator, date, and approval decision.

## Current Staging Status

The shared Foundation and Finance staging services, private Finance API, worker,
Postgres persistence, JWT context, tenant authorization, audit, idempotency,
public HTTPS, fail-closed ingress checks, and the unauthenticated `/finance`
route check have passed. The remaining acceptance action is to sign in with the
approved staging operator and submit one research request through the browser.
