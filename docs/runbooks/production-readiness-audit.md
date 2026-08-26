# Finance Production Readiness Audit

This audit is the final pre-deploy checklist for the Finance application. It
separates what is already in the repository from what still needs to be
completed in the target environment before production promotion.

Status: draft, 2026-08-26

## Repository Readiness

- [x] Finance runtime config documentation exists.
- [x] Finance local migration validation exists.
- [x] Finance staging validation exists.
- [x] Finance release operations exist.
- [x] Finance post-release verification exists.
- [x] Finance deployment manifest exists as `compose.release.yaml`.
- [x] The repo root README links to the deployment path.
- [x] A release-docs validation script exists.
- [x] A CI workflow validates the release-docs contract.

## Still Open Before Production

- [ ] Validate the release manifest in a real staging environment.
- [ ] Confirm the exact production image digest is available in the registry.
- [ ] Exercise the smoke test against the staging deployment.
- [ ] Complete or document the remaining production readiness checklist items in
      observability, rollback, and approval.
- [ ] Execute and record a restore or rollback drill for the Finance database
      change set.
- [ ] Confirm the production on-call or release owner for the promotion window.
- [ ] Confirm the named release owner and rollback owner for the target change.

## Release Gate

Finance should be treated as ready for promotion only after all of the
following are true:

1. The staging validation runbook has passed for the exact release candidate.
2. The production readiness checklist is complete or explicitly waived.
3. The release operations runbook has a named owner and rollback owner.
4. The post-release verification steps are ready to execute immediately after
   promotion.
5. The deployment manifest references the exact artifact that was validated in
   staging.
