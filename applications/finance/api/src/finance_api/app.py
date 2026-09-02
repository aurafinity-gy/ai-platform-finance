from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from finance_application import (
    CreateFinanceResearchHandler,
    DeterministicFinanceResearchWorkflow,
    EnqueueFinanceResearchHandler,
    FinanceUnitOfWorkFactory,
    PermissionDeniedError,
)
from starlette.types import Lifespan

from finance_api.routes import (
    ApiUnavailableError,
    AuthenticationRequiredError,
    FinanceResearchHandlers,
    HeaderRequestContextProvider,
    ProblemDetails,
    TenantScopeRequiredError,
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

    def problem_response(
        request: Request,
        *,
        status_code: int,
        title: str,
        detail: str,
        code: str,
    ) -> JSONResponse:
        problem = ProblemDetails(
            type=f"https://api.aurafinity.com/problems/{code}",
            title=title,
            status=status_code,
            detail=detail,
            code=code,
            correlation_id=request.headers.get("X-Correlation-ID", "unavailable"),
        )
        return JSONResponse(status_code=status_code, content=problem.model_dump())

    @app.exception_handler(AuthenticationRequiredError)
    async def authentication_required(
        request: Request, exception: AuthenticationRequiredError
    ) -> JSONResponse:
        response = problem_response(
            request,
            status_code=status.HTTP_401_UNAUTHORIZED,
            title="Authentication required",
            detail=str(exception),
            code="authentication_required",
        )
        response.headers["WWW-Authenticate"] = "Bearer"
        return response

    @app.exception_handler(TenantScopeRequiredError)
    async def tenant_scope_required(
        request: Request, exception: TenantScopeRequiredError
    ) -> JSONResponse:
        return problem_response(
            request,
            status_code=status.HTTP_400_BAD_REQUEST,
            title="Tenant scope required",
            detail=str(exception),
            code="tenant_scope_required",
        )

    @app.exception_handler(PermissionDeniedError)
    async def permission_denied(
        request: Request, exception: PermissionDeniedError
    ) -> JSONResponse:
        return problem_response(
            request,
            status_code=status.HTTP_403_FORBIDDEN,
            title="Permission denied",
            detail=str(exception),
            code="permission_denied",
        )

    @app.exception_handler(ApiUnavailableError)
    async def api_unavailable(
        request: Request, exception: ApiUnavailableError
    ) -> JSONResponse:
        return problem_response(
            request,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            title="Finance capability unavailable",
            detail=str(exception),
            code="api_unavailable",
        )

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
