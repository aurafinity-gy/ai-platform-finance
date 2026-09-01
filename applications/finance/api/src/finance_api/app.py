from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import FastAPI
from finance_application import (
    CreateFinanceResearchHandler,
    DeterministicFinanceResearchWorkflow,
    EnqueueFinanceResearchHandler,
    FinanceUnitOfWorkFactory,
)
from starlette.types import Lifespan

from finance_api.routes import (
    FinanceResearchHandlers,
    HeaderRequestContextProvider,
    router,
)


@dataclass(frozen=True, slots=True)
class SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)


class UuidGenerator:
    def new_uuid(self) -> UUID:
        return uuid4()


def create_app(
    *,
    handlers: FinanceResearchHandlers | None = None,
    context_provider: HeaderRequestContextProvider | None = None,
    uow_factory: FinanceUnitOfWorkFactory | None = None,
    lifespan: Lifespan[FastAPI] | None = None,
) -> FastAPI:
    app = FastAPI(title="AI Platform Finance API", version="0.1.0", lifespan=lifespan)
    if handlers is None:
        create_handler = CreateFinanceResearchHandler(
            workflow=DeterministicFinanceResearchWorkflow(),
            clock=SystemClock(),
            id_generator=UuidGenerator(),
            uow_factory=uow_factory,
        )
        enqueue_handler = (
            EnqueueFinanceResearchHandler(
                clock=SystemClock(),
                id_generator=UuidGenerator(),
                uow_factory=uow_factory,
            )
            if uow_factory is not None
            else None
        )
        app.state.finance_handlers = FinanceResearchHandlers(
            create=create_handler,
            enqueue=enqueue_handler,
            uow_factory=uow_factory,
        )
    else:
        app.state.finance_handlers = handlers
    app.state.context_provider = context_provider or HeaderRequestContextProvider()
    app.include_router(router)
    return app
