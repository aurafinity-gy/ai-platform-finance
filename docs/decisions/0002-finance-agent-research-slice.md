# ADR-FIN002: Finance Agent Research And Decision Slice

- Status: accepted
- Date: 2026-08-13

## Context

TradingAgents demonstrates a useful pattern for finance work: specialized
analyst agents, debate between bullish and bearish views, trader consolidation,
and an explicit risk approval step before a final decision. Finance needs the
same functional shape, but it must respect the platform rules already in place:

- generic agent execution belongs in `ai-platform-foundation`;
- Finance owns its own research meaning, policies, and outputs;
- cross-domain collaboration happens only through explicit contracts; and
- long-running work should live outside normal request handlers.

The repository currently has only one consumer contract slice and no Finance
business API yet. This ADR establishes the first Finance-owned implementation
shape before code is added.

## Decision

Finance will implement its first business slice as a paper-trading research and
decision workflow, not as a live execution engine.

The Finance bounded context will own:

- research request and response schemas;
- financial facts, calculations, assumptions, provenance, as-of time,
  confidence, and review status;
- finance-specific agent definitions and prompts;
- analyst, debate, trader, risk, and portfolio review workflow steps;
- Finance-owned persistence for the research trail and final decision; and
- Finance-specific public contracts for sharing results with other bounded
  contexts.

The Finance application will be organized around the following target package
tree:

- `applications/finance/domain`
- `applications/finance/application`
- `applications/finance/agents`
- `applications/finance/api`
- `applications/finance/persistence`
- `services/api-fastapi`
- `services/worker`

Foundation will continue to own the reusable runtime pieces:

- agent execution;
- approvals and audit primitives;
- prompt/model/provider adapters;
- workflow primitives;
- logging and observability foundations.

## Scope

The first Finance slice will support:

- one instrument or portfolio-scoped research request;
- fundamental, sentiment, news, and technical analyst outputs;
- bull/bear debate;
- trader recommendation;
- risk and portfolio approval;
- durable evidence capture; and
- a versioned result contract for downstream consumers.

## Explicit Non-Goals

- live order routing or exchange connectivity;
- generic agent execution inside Finance;
- a shared `common` or `utils` package;
- direct imports of peer repository internals;
- cross-context table queries; and
- collapsing all roles into one monolithic agent prompt.

## Consequences

- The repo gets a concrete first finance slice without overcommitting to live
  execution.
- Finance can evolve the desk logic independently while Foundation keeps the
  generic runtime reusable.
- Analyst and approval roles remain explicit, testable, and replaceable.
- Future work can add additional research agents or execution adapters without
  changing the core boundary decision.

## Follow-Up Work

1. Add the finance domain model and application ports that match this slice.
2. Add finance contracts for research request and decision output.
3. Add an API service and worker composition root for the workflow.
4. Add tests for tenant isolation, approval policy, and contract stability.

