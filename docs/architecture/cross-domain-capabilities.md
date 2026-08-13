# Finance Cross-Domain Capabilities

Status: initial consumer boundary, 2026-08-12

## Consumed capability

Finance consumes Content's `content.create_brief` v1 capability through
`POST /v1/content-briefs`. Content owns the request/response transport schema;
Finance owns the financial meaning and correctness of the facts it places in
`domain_context`, `research`, and `sources`.

The pinned provider schema is
[`../../contracts/providers/content/content.openapi.v1.json`](../../contracts/providers/content/content.openapi.v1.json).
Its SHA-256 and upstream source are recorded in the acceptance record. Finance
fixtures are independently validated against the request and accepted-response
schemas by the Finance test suite.

The future Finance adapter must:

- obtain authentication through Foundation-aligned composition;
- send the untrusted tenant selector while relying on Content to verify current
  membership and `content.brief.create` permission;
- use a stable request ID and idempotency key;
- preserve source reference, provenance, assumptions, currency/units,
  precision, as-of time, confidence, and Finance review status;
- treat Content errors as stable boundary errors and avoid importing Content
  implementation code; and
- log only safe identifiers, never raw research, prompts, credentials, or
  sensitive financial information.

## Current capabilities

- Finance currently consumes Content's `content.create_brief` v1 capability.
- Finance owns the input facts it supplies to that capability.
- Contract fixtures and acceptance evidence exist for the consumer boundary.

## Future capabilities

- Finance-owned financial research contracts.
- Finance-owned analysis/query contracts for portfolios, securities, and
  budgets.
- Finance-specific agent or workflow contracts when a named consumer exists.

## Provided capabilities

No Finance-provided capability is declared yet. A future financial-research
contract must be owned here and must define facts, calculations, assumptions,
sources, timestamps, classification, quality metadata, tenant scope,
authorization, audit, and compatibility. Content must not define it on
Finance's behalf.
