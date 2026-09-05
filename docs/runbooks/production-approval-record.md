# Finance Production Approval Record

## Ownership

- Release owner: Gary Yee <gary.yee@aurafinity.com>
- Rollback owner: Gary Yee <gary.yee@aurafinity.com>

One-person release and rollback ownership is approved for the bounded initial
canary, provided the change record includes the rollback procedure and stop
criteria.

## Required Independent Approval

- Security reviewer: Damon Yee <damon.yee@aurafinity.com>
- Change approver: Damon Yee <damon.yee@aurafinity.com>
- Production on-call escalation: Damon Yee <damon.yee@aurafinity.com>

Approval status:

- Approved by: Damon Yee <damon.yee@aurafinity.com>
- Approved on: 2026-09-04
- Approved scope: production change window and bounded Finance canary
- Exact execution window: `2026-09-05 03:52:22 UTC` to `2026-09-05 03:52:22 UTC`
- Allowlisted production tenant: `Aurafinity Inc.`
- Allowlisted production user: Gary Yee <gary.yee@aurafinity.com>

Promoted production artifacts:

- Finance API image: `acrafinprodmpn729.azurecr.io/finance-api-fastapi:8f34207`
  at `sha256:5ce5678309740ae983236a3289ee70da9485ae3be8db8e84baa4671435e1ed4d`
- Finance worker image: `acrafinprodmpn729.azurecr.io/finance-worker:8f34207`
  at `sha256:f6c4d653dac2f089b5aa0a59fe3ec67f46c9e824f16913e4b235331c984407ab`
- Foundation web image: `acrafinprodmpn729.azurecr.io/web:sha-54e0740d7017`
  at `sha256:954d1bd09ed337fbe3f6f229e93e511f8370dca7ac6f1ac76c790f3ddd25b37e`

The release owner and rollback owner may be the same person. Independent security,
change, and escalation ownership is recorded separately for this release. The
approved canary remains paper-research-only with no broker write access.

## Evidence

### Bounded Production Canary Closure

- Canary user signed in successfully and selected `Aurafinity Inc.`.
- Finance research job `4d2a1638-48eb-4803-a33a-865a3e9b9f1e` completed with
  status `succeeded` at `2026-09-05 03:52:22.864861 UTC`.
- Job creation began at `2026-09-05 03:52:22.838897 UTC`.
- Research record `f6363ac1-b340-481c-86df-2144f5c42b11` was accepted at
  `2026-09-05 03:52:22.858734 UTC`, with recommendation `sell` and confidence
  `0.35`.
- Audit entry `finance.research.created` was recorded with result `success` at
  `2026-09-05 03:52:22.858734 UTC`.
- No broker or live-trading capability was enabled; the canary remained
  paper-research-only.
- The Finance-enabled web image was running healthy, and the durable
  `platform-compose-start.service` was enabled with the web override path in
  `/srv/platform/config/release.env`.
- Damon Yee reviewed the production canary evidence and approved bounded canary
  closure on `2026-09-05`.

- Staging evidence: [`staging-evidence-2026-09-04.md`](staging-evidence-2026-09-04.md)
- Readiness checklist: [`production-readiness-checklist.md`](production-readiness-checklist.md)
- Release operations: [`release-operations.md`](release-operations.md)
