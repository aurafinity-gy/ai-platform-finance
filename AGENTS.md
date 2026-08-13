# AI Platform Finance — Agent Instructions

## Repository purpose

This repository owns the Finance bounded context. It owns financial facts,
calculations, assumptions, research semantics, review policy, and Finance-owned
provider mappings. It does not own generic platform infrastructure or another
application's business rules.

## Architectural authority

Read these sources before significant work:

1. `../ai-platform-handbook/README.md` and the task-relevant numbered volumes.
2. `../ai-platform-foundation/AGENTS.md` and its implementation-readiness docs.
3. This file and `docs/architecture/`.

The handbook governs architecture. Foundation is the reusable implementation
authority. Conflicts must be documented and resolved deliberately.

## Ecosystem boundaries

This repository participates in a peer-repository ecosystem with the following
shared boundary rules:

- `ai-platform-foundation` is the reusable implementation authority.
- Peer repositories own their own business meaning and collaborate through
  explicit versioned contracts.
- Generic capabilities belong in foundation rather than in a shared or common
  package.
- Finance may consume Content, Events, and future domain capabilities only
  through public contracts, never by importing peer internals or querying their
  private tables.
- Finance-specific agents, prompts, and workflows stay here; generic agent
  execution stays in foundation.

## Domain ownership

Finance owns financial research, financial facts and calculations, assumptions,
currency and precision semantics, source provenance, as-of time, confidence,
review status, and Finance-specific integrations.

Content owns briefs, writing, editorial review, and publishing. Events owns
event planning and logistics. Finance consumes peer capabilities only through
explicit public contracts and never imports peer internals or queries their
private tables.

## Foundation-first

Inspect Foundation before implementing authentication, tenancy, authorization,
audit, idempotency, workflow, agent execution, model invocation, configuration,
HTTP, persistence, jobs, secrets, retries, or observability. Reusable generic
capabilities belong upstream; Finance business meaning stays here.

## Dependency and data rules

Dependencies point inward: API/worker/adapters -> application -> domain. Domain
code imports no frameworks, providers, storage, transport, or environment
configuration. Provider SDKs remain in named adapters. Finance owns its records
and mappings; shared PostgreSQL infrastructure does not grant cross-domain data
access. Tenant isolation, current membership, permission checks, RLS, audit,
safe telemetry, and idempotency are mandatory where applicable.

## Contract stability

Cross-domain contracts are versioned and tested. Provider OpenAPI snapshots are
pinned under `contracts/providers/`; they are not hand-edited. Finance-owned
fixtures and consumer tests verify semantic compatibility. Additive optional
changes may remain in a major version; removed, renamed, or redefined fields
require a new version and migration plan.

## Current scope

The first repository slice confirms Finance as a consumer of Content's
`content.create_brief` v1 capability. It does not yet implement financial
research, persistence, external providers, a web application, or agents. Add
those only as named, independently reviewed vertical slices.
