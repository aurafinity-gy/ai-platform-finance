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

The initial slice establishes the repository boundary and independently tests
Finance's use of Content's `content.create_brief` v1 contract. No financial
research implementation or provider integration is implied yet.

Start with:

- [Agent instructions](AGENTS.md)
- [Finance domain ownership](docs/architecture/domain-ownership.md)
- [Cross-domain capabilities](docs/architecture/cross-domain-capabilities.md)
- [Finance package tree](docs/architecture/package-tree.md)
- [Finance runtime config](docs/runbooks/finance-runtime-config.md)
- [Finance local migration validation](docs/runbooks/local-finance-migration.md)
- [Finance agent research ADR](docs/decisions/0002-finance-agent-research-slice.md)
- [Content consumer decision](docs/decisions/0001-content-brief-consumer.md)
- [Content contract acceptance](contracts/acceptance/content-brief-v1.json)

Run the repository checks:

```powershell
uv sync --locked
uv run ruff format --check .
uv run ruff check .
uv run pytest
```
