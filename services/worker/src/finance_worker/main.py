import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from finance_application import (
    CreateFinanceResearch,
    CreateFinanceResearchHandler,
    RequestContext,
)
from finance_persistence import InMemoryFinanceUnitOfWorkFactory


@dataclass(slots=True)
class FinanceResearchWorker:
    handler: CreateFinanceResearchHandler
    context: RequestContext
    queue: asyncio.Queue[CreateFinanceResearch] = field(default_factory=asyncio.Queue)
    results: list[dict[str, Any]] = field(default_factory=list)

    async def submit(self, command: CreateFinanceResearch) -> None:
        await self.queue.put(command)

    async def process_one(self) -> bool:
        try:
            command = self.queue.get_nowait()
        except asyncio.QueueEmpty:
            return False
        result = await self.handler.execute(command, self.context)
        self.results.append(
            {
                "finance_research_id": str(result.finance_research_id),
                "request_id": str(result.request_id),
                "recommendation": result.recommendation,
                "status": result.status,
            }
        )
        self.queue.task_done()
        return True

    async def serve(self) -> None:
        while True:
            processed = await self.process_one()
            if not processed:
                await asyncio.sleep(0.1)


def create_runtime_worker() -> FinanceResearchWorker:
    uow_factory = InMemoryFinanceUnitOfWorkFactory()
    actor_id = UUID("30000000-0000-0000-0000-000000000001")
    tenant_id = UUID("30000000-0000-0000-0000-000000000002")
    uow_factory.grant_permission(
        actor_id=actor_id,
        tenant_id=tenant_id,
        permission="finance.research.create",
    )
    handler = CreateFinanceResearchHandler(
        clock=_SystemClock(),
        id_generator=_UuidGenerator(),
        uow_factory=uow_factory,
    )
    return FinanceResearchWorker(
        handler=handler,
        context=RequestContext(
            actor_id=actor_id,
            tenant_id=tenant_id,
            correlation_id="corr-30000000-0000-0000-0000-000000000003",
        ),
    )


@dataclass(frozen=True, slots=True)
class _SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)


class _UuidGenerator:
    def new_uuid(self) -> UUID:
        return uuid4()


def run() -> None:
    asyncio.run(create_runtime_worker().serve())


if __name__ == "__main__":
    run()
