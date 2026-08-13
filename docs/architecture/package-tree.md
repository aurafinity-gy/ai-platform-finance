# Finance Package Tree

Status: target architecture, 2026-08-13

This repository currently contains boundary documentation and one consumer
contract slice. The tree below is the first concrete Finance implementation
shape for a TradingAgents-style research and decision workflow.

## Target layout

```text
ai-platform-finance/
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
    consumers/
    fixtures/
    providers/
      content/
      market-data/
      news/
  docs/
    architecture/
    decisions/
    runbooks/
  services/
    api-fastapi/
    worker/
  tests/
    architecture/
    contracts/
    integration/
```

## Package responsibilities

`applications/finance/domain`
: Finance-owned facts, calculations, assumptions, provenance, confidence,
  as-of time, review status, and the canonical shapes for research requests,
  research packages, signals, proposals, and decisions.

`applications/finance/application`
: Use cases and orchestration logic. This layer coordinates analyst, debate,
  trader, risk, and portfolio flows through ports, but does not embed
  provider SDKs or transport code.

`applications/finance/agents`
: Finance-specific agent definitions, prompts, tool contracts, debate rules,
  and memory schemas. Generic agent execution remains in Foundation.

`applications/finance/api`
: Finance HTTP contract surface for commands, queries, and workflow actions.
  FastAPI handlers translate transport concerns into application calls.

`applications/finance/persistence`
: Finance-owned persistence adapters and repository implementations.
  This layer is replaceable infrastructure behind application ports.

`contracts`
: Versioned, testable boundary contracts. Consumer fixtures and acceptance
  evidence live here alongside pinned provider schemas.

`services/api-fastapi`
: Finance HTTP composition root for public endpoints.

`services/worker`
: Finance background composition root for long-running research and approval
  workflows if the first slice needs asynchronous execution.

## First vertical slice

The first finance slice should implement a paper-trading research workflow:

1. Accept a research request for one instrument or portfolio scope.
2. Gather evidence from finance-owned provider adapters.
3. Run specialized analyst agents for fundamental, sentiment, news, and
   technical views.
4. Run a debate pass that exposes bull and bear arguments.
5. Produce a trader recommendation.
6. Run risk and portfolio approval checks.
7. Persist the full evidence trail and final decision.
8. Publish a versioned result that another bounded context can consume.

## Constraints

- No live order execution in the first slice.
- No generic agent runtime in Finance.
- No peer repository internals imported into Finance.
- No direct database access across bounded contexts.
- No provider SDKs in the domain layer.

