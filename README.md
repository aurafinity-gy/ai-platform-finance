# AI Platform Finance

`ai-platform-finance` owns Finance domain semantics and Finance-provided
capabilities for the AI application ecosystem.

This repository follows the shared ecosystem boundary rules:

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

Current capabilities:

- Repository boundary and ownership rules.
- Consumer tests for Content's `content.create_brief` v1 contract.
- Contract validation fixtures and acceptance evidence.

Future capabilities:

- Financial research and analysis.
- Portfolio, security, and budget analysis.
- Finance-owned provider integrations.
- Finance-specific commands, queries, and agent workflows.
- A TradingAgents-style research and decision pipeline with explicit analyst,
  debate, trader, risk, and portfolio stages.

The initial slice now includes a deterministic paper-trading research workflow
and durable Finance persistence. External market-data providers, Foundation
agent-runtime integration, human approval, and live execution remain future
capabilities.

Start with:

- [Agent instructions](AGENTS.md)
- [Finance domain ownership](docs/architecture/domain-ownership.md)
- [Cross-domain capabilities](docs/architecture/cross-domain-capabilities.md)
- [Finance package tree](docs/architecture/package-tree.md)
- [Finance research job queue](docs/architecture/research-job-queue.md)
- [Finance application definition](docs/architecture/application-definition.md)
- [Finance MVP application acceptance](docs/runbooks/mvp-application-acceptance.md)
- [Application definition starter](../ai-platform-handbook/volume-03-applications/templates.md#application-definition-starter)
- [Finance application definition example](../ai-platform-handbook/volume-03-applications/application-definition-finance-example.md)
- [Finance runtime config](docs/runbooks/finance-runtime-config.md)
- [Finance local migration validation](docs/runbooks/local-finance-migration.md)
- [Finance staging validation](docs/runbooks/staging-validation.md)
- [Finance production readiness checklist](docs/runbooks/production-readiness-checklist.md)
- [Finance release operations](docs/runbooks/release-operations.md)
- [Finance post-release verification](docs/runbooks/post-release.md)
- [Finance deployment manifest](docs/runbooks/deployment-manifest.md)
- [Finance production readiness audit](docs/runbooks/production-readiness-audit.md)
- [Finance smoke test](scripts/finance-smoke-test.ps1)
- [Finance staging validation script](scripts/finance-staging-validation.ps1)
- [Shared release and deployment entry point](../ai-platform-handbook/volume-11-delivery-workflows/deployment-and-release-entry-point.md)
- [Finance agent research ADR](docs/decisions/0002-finance-agent-research-slice.md)
- [Content consumer decision](docs/decisions/0001-content-brief-consumer.md)
- [Content contract acceptance](contracts/acceptance/content-brief-v1.json)

## Quick Checks

```powershell
uv sync --locked
uv run ruff format --check .
uv run ruff check .
uv run pytest
pwsh -File scripts/finance-smoke-test.ps1
```
