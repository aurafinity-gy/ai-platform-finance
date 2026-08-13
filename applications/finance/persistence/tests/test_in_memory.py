import asyncio
from datetime import UTC, datetime
from uuid import UUID

from finance_application import (
    AuditEntry,
    CommandScope,
    RequestContext,
    StoredCommandResult,
)
from finance_persistence import InMemoryFinanceUnitOfWorkFactory


def test_in_memory_finance_unit_of_work_stores_and_replays() -> None:
    factory = InMemoryFinanceUnitOfWorkFactory()
    actor_id = UUID("30000000-0000-0000-0000-000000000001")
    tenant_id = UUID("30000000-0000-0000-0000-000000000002")
    factory.grant_permission(
        actor_id=actor_id,
        tenant_id=tenant_id,
        permission="finance.research.create",
    )
    context = RequestContext(
        actor_id=actor_id,
        tenant_id=tenant_id,
        correlation_id="corr-30000000-0000-0000-0000-000000000003",
    )
    scope = CommandScope(
        tenant_id=tenant_id,
        actor_id=actor_id,
        operation="finance.research.create",
        key_hash="abc123",
    )
    stored = StoredCommandResult(
        scope=scope,
        fingerprint="fingerprint",
        response_status=201,
        result={
            "finance_research_id": "30000000-0000-0000-0000-000000000011",
            "request_id": "30000000-0000-0000-0000-000000000010",
            "source_domain": "finance",
            "source_reference": "portfolio-ops/weekly-research",
            "instrument": "AAPL",
            "recommendation": "buy",
            "confidence": "0.750000",
            "correlation_id": "corr-30000000-0000-0000-0000-000000000003",
            "created_at": datetime(2026, 8, 13, 15, 5, tzinfo=UTC).isoformat(),
            "contract_version": "1",
            "status": "accepted",
            "issues": "[]",
            "replayed": "false",
        },
        target_id=UUID("30000000-0000-0000-0000-000000000011"),
        correlation_id=context.correlation_id,
        created_at=datetime(2026, 8, 13, 15, 5, tzinfo=UTC),
        expires_at=datetime(2026, 8, 14, 15, 5, tzinfo=UTC),
    )

    async def exercise() -> None:
        async with factory.create(context) as uow:
            assert await uow.memberships.has_permission(
                actor_id=actor_id,
                tenant_id=tenant_id,
                permission="finance.research.create",
            )
            assert await uow.idempotency.lock_and_get(scope) is None
            await uow.idempotency.add(stored)
            replayed = await uow.idempotency.lock_and_get(scope)
            assert replayed is not None
            await uow.audit.add(
                AuditEntry(
                    entry_id=UUID("30000000-0000-0000-0000-000000000099"),
                    context=context,
                    action="finance.research.created",
                    target_type="finance_research",
                    target_id=stored.target_id,
                    result="success",
                    risk="medium",
                    occurred_at=datetime(2026, 8, 13, 15, 5, tzinfo=UTC),
                    metadata={"contract_version": "1"},
                )
            )

    asyncio.run(exercise())
    assert len(factory.state.audit_entries) == 1

