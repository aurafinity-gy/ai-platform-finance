# Finance Production Readiness Audit

This audit is a short-form summary of what still needs to be true before the
Finance application should be treated as production-deployable.

Status: draft, 2026-08-26

## Already In Place

- Finance runtime config documentation exists.
- Finance local migration validation exists.
- Finance staging validation exists.
- Finance release operations exist.
- Finance post-release verification exists.
- Finance deployment manifest exists as `compose.release.yaml`.
- The repo root README links to the deployment path.

## Still Open Before Production

- Validate the release manifest in a real staging environment.
- Confirm the exact production image digest is available in the registry.
- Exercise the smoke test against the staging deployment.
- Complete or document the remaining production readiness checklist items in
  observability, rollback, and approval.
- Execute and record a restore or rollback drill for the Finance database
  change set.
- Confirm the production on-call or release owner for the promotion window.

## Release Gate

Finance should be treated as ready for promotion only after:

1. The staging validation runbook has passed for the exact release candidate.
2. The production readiness checklist is complete or explicitly waived.
3. The release operations runbook has a named owner and rollback owner.
4. The post-release verification steps are ready to execute immediately after
   promotion.

