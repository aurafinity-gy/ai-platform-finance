from asyncio import run
from datetime import UTC, datetime
from uuid import UUID

from finance_application import (
    CreateFinanceResearch,
    CreateFinanceResearchHandler,
    DeterministicFinanceResearchWorkflow,
    EnqueueFinanceResearchHandler,
    RequestContext,
)
from finance_persistence import InMemoryFinanceUnitOfWorkFactory


class FixedClock:
    def now(self) -> datetime:
        return datetime(2026, 8, 13, 15, 5, tzinfo=UTC)


class FixedUuidGenerator:
    def __init__(self) -> None:
        self._values = iter(
            [UUID("30000000-0000-0000-0000-000000000011")]
        )

    def new_uuid(self) -> UUID:
        return next(self._values)


def test_finance_research_handler_executes_workflow() -> None:
    handler = CreateFinanceResearchHandler(
        workflow=DeterministicFinanceResearchWorkflow(),
        clock=FixedClock(),
        id_generator=FixedUuidGenerator(),
    )
    command = CreateFinanceResearch(
        request_id=UUID("30000000-0000-0000-0000-000000000010"),
        source_domain="finance",
        source_reference="portfolio-ops/weekly-research",
        instrument="AAPL",
        objective=(
            "Evaluate whether Apple stock is suitable for a medium-term long position."
        ),
        thesis="Services growth and capital returns support upside.",
        horizon_days=90,
        domain_context={
            "as_of": "2026-08-13T15:00:00Z",
            "sentiment": "positive",
        },
        research=(),
        sources=(),
        constraints=("paper-trading only", "do not execute live orders"),
        quality_metadata={"review_status": "finance-reviewed"},
        idempotency_key="abc123",
    )
    context = RequestContext(
        actor_id=UUID("30000000-0000-0000-0000-000000000001"),
        tenant_id=UUID("30000000-0000-0000-0000-000000000002"),
        correlation_id="corr-30000000-0000-0000-0000-000000000003",
    )

    result = run(handler.execute(command, context))

    assert result.finance_research_id == UUID("30000000-0000-0000-0000-000000000011")
    assert result.status == "accepted"
    assert result.recommendation in {"buy", "hold", "sell"}


def test_enqueue_finance_research_persists_a_job() -> None:
    actor_id = UUID("30000000-0000-0000-0000-000000000001")
    tenant_id = UUID("30000000-0000-0000-0000-000000000002")
    factory = InMemoryFinanceUnitOfWorkFactory(
        memberships={(actor_id, tenant_id): {"finance.research.create"}}
    )
    handler = EnqueueFinanceResearchHandler(
        clock=FixedClock(),
        id_generator=FixedUuidGenerator(),
        uow_factory=factory,
    )
    command = CreateFinanceResearch(
        request_id=UUID("30000000-0000-0000-0000-000000000010"),
        source_domain="finance",
        source_reference="queue-test",
        instrument="AAPL",
        objective="Evaluate the instrument.",
        thesis=None,
        horizon_days=None,
        domain_context={"as_of": "2026-08-13T15:00:00Z"},
        research=(),
        sources=(),
        constraints=(),
        quality_metadata={},
        idempotency_key="queue-key",
    )
    context = RequestContext(
        actor_id=actor_id,
        tenant_id=tenant_id,
        correlation_id="corr-queue",
    )

    result = run(handler.execute(command, context))

    assert result.status == "queued"
    assert factory.state.jobs[0].request_id == command.request_id

