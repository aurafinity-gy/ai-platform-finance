# ADR-FIN001: Consume Content Brief Intake v1

- Status: accepted
- Date: 2026-08-12

## Context

Finance needs a bounded way to request Content work without transferring
financial authority or importing Content internals. Content publishes
`content.create_brief` as `POST /v1/content-briefs` with an OpenAPI contract.

## Decision

Finance accepts the v1 request and accepted-response shapes as its initial
Content integration boundary. Finance pins the provider OpenAPI artifact,
authors Finance-specific fixtures, and validates them in a consumer-owned test.
The future runtime adapter will depend on the HTTP contract only.

Finance remains authoritative for financial facts, calculations, assumptions,
provenance, timestamps, confidence, and review status. Content remains
authoritative for intake, writing, editorial workflow, and publishing.

## Consequences

- Provider implementation, persistence, framework types, and private tables do
  not cross the boundary.
- Additive optional v1 changes are compatible; semantic or required-field
  breakage requires a new version and migration plan.
- The pinned snapshot must be refreshed deliberately and the Finance consumer
  tests rerun before accepting provider changes.
- This ADR confirms contract compatibility, not production deployment or a
  completed Finance-to-Content runtime adapter.

