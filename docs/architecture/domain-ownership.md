# Finance Domain Ownership

Status: architecture baseline, 2026-08-12

Finance owns the meaning and lifecycle of financial facts, calculations,
assumptions, research packages, provenance, currency and precision, as-of time,
confidence, and Finance review status. Finance remains authoritative when those
facts are supplied to another bounded context.

## Ecosystem boundaries

The shared rules for this repository and the sibling domains are:

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

Finance does not own Content briefs, writing, editorial decisions, channels, or
publishing. It does not own generic authentication, tenancy, authorization,
audit, workflow, agent runtime, model invocation, HTTP, secrets, retry, or
observability infrastructure.

## Current capabilities

- Repository boundary and ownership rules.
- Consumer validation of Content's `content.create_brief` v1 contract.
- Contract fixtures, acceptance evidence, and review notes.
- No Finance-owned business API, research pipeline, or provider integration
  slice yet.

## Future capabilities

- Financial research and analysis contracts.
- Portfolio, security, and budget analysis contracts.
- Finance-owned provider adapters and command/query APIs.
- Finance agent workflows and publication support if a named consumer appears.

Cross-domain collaboration uses stable references and versioned capability
contracts. No peer source imports, shared domain models, cross-domain table
queries, provider objects, or database identifiers may cross the boundary.

The current repository contains no Finance aggregate or source-of-truth data.
Those will be introduced with the first Finance-owned vertical slice, including
an ADR, data classification, authorization, tenant isolation, audit,
observability, and verification evidence.
