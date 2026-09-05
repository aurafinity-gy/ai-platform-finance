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
- Exact execution window: **To be recorded before deployment**
- Allowlisted production tenant: `Aurafinity Inc.` (production tenant ID to be verified)
- Allowlisted production user: Gary Yee <gary.yee@aurafinity.com>

Promoted production artifacts:

- Finance API image: `acrafinprodmpn729.azurecr.io/finance-api-fastapi:8f34207`
  at `sha256:5ce5678309740ae983236a3289ee70da9485ae3be8db8e84baa4671435e1ed4d`
- Finance worker image: `acrafinprodmpn729.azurecr.io/finance-worker:8f34207`
  at `sha256:f6c4d653dac2f089b5aa0a59fe3ec67f46c9e824f16913e4b235331c984407ab`

The release owner and rollback owner may be the same person. Independent security,
change, and escalation ownership is recorded separately for this release. The
approved canary remains paper-research-only with no broker write access.

## Evidence

- Staging evidence: [`staging-evidence-2026-09-04.md`](staging-evidence-2026-09-04.md)
- Readiness checklist: [`production-readiness-checklist.md`](production-readiness-checklist.md)
- Release operations: [`release-operations.md`](release-operations.md)
