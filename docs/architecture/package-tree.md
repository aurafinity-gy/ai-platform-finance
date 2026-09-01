# Finance Package Tree

Status: implemented baseline, 2026-08-13

This repository now contains the first concrete Finance implementation shape
for a TradingAgents-style research and decision workflow. The tree below
reflects the checked-in workspace rather than a future target.

## Implemented layout

```text
ai-platform-finance/
  CONTRIBUTING.md
  README.md
  scripts/
    finance-smoke-test.ps1
  applications/
    finance/
      domain/
        src/
          finance_domain/
        tests/
      application/
        src/
          finance_application/
        tests/
      agents/
        src/
          finance_agents/
            roles.py
        tests/
      api/
        src/
          finance_api/
        tests/
      persistence/
        src/
          finance_persistence/
        tests/
  contracts/
    acceptance/
    fixtures/
    providers/
      finance/
      content/
  docs/
    architecture/
      cross-domain-capabilities.md
      domain-ownership.md
      package-tree.md
      source-control.md
    decisions/
      0001-content-brief-consumer.md
      0002-finance-agent-research-slice.md
      0003-finance-runtime-uses-postgres-and-jwt-context.md
    runbooks/
      finance-runtime-config.md
      local-finance-migration.md
      production-readiness-checklist.md
  infrastructure/
    supabase/
      migrations/
        202608130000_platform_audit_entries.sql
        202608130001_finance_research.sql
  services/
    api-fastapi/
      src/
        finance_api_service/
      tests/
    worker/
      src/
        finance_worker/
      tests/
  tests/
    contracts/
```

## Package Responsibilities

`applications/finance/domain`
: Finance-owned facts, calculations, assumptions, provenance, confidence,
  as-of time, review status, and the canonical shapes for research requests,
  research packages, signals, proposals, and decisions.

`applications/finance/application`
: Use cases and orchestration logic. This layer coordinates analyst, debate,
  trader, risk, and portfolio flows through ports, but does not embed
  provider SDKs or transport code.

`applications/finance/agents`
: Finance-specific role definitions, typed assessments, prompts, tool
  contracts, debate rules, and memory schemas. Generic agent execution remains
  in Foundation.

`applications/finance/api`
: Finance HTTP contract surface for commands, queries, and workflow actions.
  FastAPI handlers translate transport concerns into application calls.

`applications/finance/persistence`
: Finance-owned persistence adapters and repository implementations. This
  layer is replaceable infrastructure behind application ports.

`contracts`
: Versioned, testable boundary contracts. Acceptance fixtures and provider
schemas live here.

`docs/architecture`
: Repository architecture, ownership, and source-control guidance.

`docs/decisions`
: Decision records for the finance slice and runtime composition choices.

`docs/runbooks`
: Operational notes for local and deployed runtime configuration.

`infrastructure/supabase/migrations`
: Additive SQL migrations for the Finance schema and command replay tables.

`services/api-fastapi`
: Finance HTTP composition root for public endpoints.

`services/worker`
: Finance background composition root for long-running research and approval
  workflows if the first slice needs asynchronous execution.

## Current Vertical Slice

The current finance slice implements a paper-trading research workflow with:

1. Request validation and transport-to-command mapping.
2. JWT-derived request context and tenant scope.
3. Permission checks through Finance-owned membership lookups.
4. Idempotent command handling.
5. Durable research record persistence.

The deterministic first workflow currently evaluates fundamental, sentiment,
news, and technical views, followed by bull/bear synthesis. These are the
initial Finance-owned role behaviors; the `agents` package remains the home for
extracting them into explicit agent definitions backed by Foundation's runtime.
6. Audit writes for accepted workflow actions.
7. A versioned accepted-response contract for downstream consumers.

## Constraints

- No live order execution in the first slice.
- The worker's production entry point requires Postgres and a provisioned
  service identity; in-memory persistence is test-only.
- No generic agent runtime in Finance.
- No peer repository internals imported into Finance.
- No direct database access across bounded contexts.
- No provider SDKs in the domain layer.
