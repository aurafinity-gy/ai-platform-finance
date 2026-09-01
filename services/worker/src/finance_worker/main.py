import asyncio
import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from finance_application import (
    CreateFinanceResearch,
    CreateFinanceResearchHandler,
    DeterministicFinanceResearchWorkflow,
    RequestContext,
)
from finance_persistence import (
    InMemoryFinanceUnitOfWorkFactory,
    PostgresFinanceUnitOfWorkFactory,
)
from psycopg_pool import AsyncConnectionPool


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
    """Create an in-memory worker for tests and local workflow exercises."""
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
class WorkerRuntimeSettings:
    database_url: str
    actor_id: UUID
    tenant_id: UUID

    @classmethod
    def from_environment(
        cls, environment: Mapping[str, str] | None = None
    ) -> "WorkerRuntimeSettings":
        values = environment or os.environ
        required = {
            "FINANCE_DATABASE_URL": values.get("FINANCE_DATABASE_URL", "").strip(),
            "FINANCE_WORKER_ACTOR_ID": values.get(
                "FINANCE_WORKER_ACTOR_ID", ""
            ).strip(),
            "FINANCE_WORKER_TENANT_ID": values.get(
                "FINANCE_WORKER_TENANT_ID", ""
            ).strip(),
        }
        missing = sorted(key for key, value in required.items() if not value)
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")
        try:
            actor_id = UUID(required["FINANCE_WORKER_ACTOR_ID"])
            tenant_id = UUID(required["FINANCE_WORKER_TENANT_ID"])
        except ValueError as exc:
            raise ValueError(
                "FINANCE_WORKER_ACTOR_ID and FINANCE_WORKER_TENANT_ID must be UUIDs."
            ) from exc
        return cls(
            database_url=required["FINANCE_DATABASE_URL"],
            actor_id=actor_id,
            tenant_id=tenant_id,
        )


async def serve_runtime_worker(
    settings: WorkerRuntimeSettings | None = None,
) -> None:
    runtime = settings or WorkerRuntimeSettings.from_environment()
    pool = AsyncConnectionPool(
        runtime.database_url,
        min_size=1,
        max_size=10,
        open=False,
    )
    await pool.open()
    try:
        worker = FinanceResearchWorker(
            handler=CreateFinanceResearchHandler(
                workflow=DeterministicFinanceResearchWorkflow(),
                clock=_SystemClock(),
                id_generator=_UuidGenerator(),
                uow_factory=PostgresFinanceUnitOfWorkFactory(pool),
            ),
            context=RequestContext(
                actor_id=runtime.actor_id,
                tenant_id=runtime.tenant_id,
                correlation_id=f"finance-worker:{runtime.actor_id}",
            ),
        )
        await worker.serve()
    finally:
        await pool.close()


@dataclass(frozen=True, slots=True)
class _SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)


class _UuidGenerator:
    def new_uuid(self) -> UUID:
        return uuid4()


def run() -> None:
    asyncio.run(serve_runtime_worker())


if __name__ == "__main__":
    run()
