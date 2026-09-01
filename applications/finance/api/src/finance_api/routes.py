import json
from dataclasses import dataclass
from datetime import datetime
from typing import Annotated, Any, Literal, Protocol, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request, status
from finance_application import (
    CreateFinanceResearch,
    CreateFinanceResearchHandler,
    EnqueueFinanceResearchHandler,
    FinanceResearchAcceptedResult,
    FinanceResearchQueuedResult,
    RequestContext,
)
from finance_domain import ResearchMaterial, SourceMaterial
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

router = APIRouter(prefix="/v1/finance-researches", tags=["Finance"])


class AuthenticationRequiredError(PermissionError):
    """Raised when the deployment edge cannot establish an actor context."""


class TenantScopeRequiredError(ValueError):
    """Raised when the caller has not selected a tenant."""


class ApiUnavailableError(RuntimeError):
    """Raised when the executable composition has not supplied a handler."""


class RequestContextProvider(Protocol):
    async def resolve(self, request: Request) -> RequestContext: ...


@dataclass(frozen=True, slots=True)
class FinanceResearchHandlers:
    create: CreateFinanceResearchHandler
    enqueue: EnqueueFinanceResearchHandler | None = None


class HeaderRequestContextProvider:
    async def resolve(self, request: Request) -> RequestContext:
        actor_id = request.headers.get("X-Actor-Id")
        tenant_id = request.headers.get("X-Tenant-Id")
        correlation_id = request.headers.get("X-Correlation-Id")
        if not actor_id or not tenant_id or not correlation_id:
            raise TenantScopeRequiredError(
                "X-Actor-Id, X-Tenant-Id, and X-Correlation-Id are required."
            )
        return RequestContext(
            actor_id=UUID(actor_id),
            tenant_id=UUID(tenant_id),
            correlation_id=correlation_id,
        )


class ResearchMaterialRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str = Field(min_length=1, max_length=2_000)
    facts: list[str] = Field(default_factory=list, max_length=100)


class SourceMaterialRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_reference: str = Field(min_length=1, max_length=500)
    title: str = Field(min_length=1, max_length=300)
    url: HttpUrl | None = None
    as_of: datetime | None = None


class CreateFinanceResearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contract_version: Literal[1]
    request_id: UUID
    source_domain: str = Field(min_length=1, max_length=64)
    source_reference: str = Field(min_length=1, max_length=500)
    instrument: str = Field(min_length=1, max_length=20)
    objective: str = Field(min_length=1, max_length=1_000)
    thesis: str | None = Field(default=None, min_length=1, max_length=1_000)
    horizon_days: int | None = Field(default=None, ge=1)
    domain_context: dict[str, Any]
    research: list[ResearchMaterialRequest] = Field(
        default_factory=list, max_length=100
    )
    sources: list[SourceMaterialRequest] = Field(default_factory=list, max_length=100)
    constraints: list[str] = Field(default_factory=list, max_length=100)
    quality_metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def bounded_structured_context(self) -> "CreateFinanceResearchRequest":
        structured = json.dumps(
            {
                "domain_context": self.domain_context,
                "research": [item.model_dump(mode="json") for item in self.research],
                "sources": [item.model_dump(mode="json") for item in self.sources],
                "quality_metadata": self.quality_metadata,
            },
            separators=(",", ":"),
        )
        if len(structured.encode()) > 64 * 1024:
            raise ValueError("Structured Finance research context exceeds 64 KiB.")
        return self

    def to_command(self, idempotency_key: str) -> CreateFinanceResearch:
        return CreateFinanceResearch(
            request_id=self.request_id,
            source_domain=self.source_domain,
            source_reference=self.source_reference,
            instrument=self.instrument,
            objective=self.objective,
            thesis=self.thesis,
            horizon_days=self.horizon_days,
            domain_context=self.domain_context,
            research=tuple(
                ResearchMaterial.create(item.summary, tuple(item.facts))
                for item in self.research
            ),
            sources=tuple(
                SourceMaterial.create(
                    source_reference=item.source_reference,
                    title=item.title,
                    url=str(item.url) if item.url else None,
                    as_of=item.as_of,
                )
                for item in self.sources
            ),
            constraints=tuple(self.constraints),
            quality_metadata=self.quality_metadata,
            idempotency_key=idempotency_key,
            contract_version=self.contract_version,
        )


class FinanceResearchAcceptedResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contract_version: Literal[1]
    finance_research_id: UUID
    request_id: UUID
    source_domain: str
    source_reference: str
    instrument: str
    recommendation: str
    confidence: float
    issues: list[str]
    correlation_id: str
    created_at: datetime
    replayed: bool
    status: Literal["accepted"]

    @classmethod
    def from_result(
        cls, result: FinanceResearchAcceptedResult
    ) -> "FinanceResearchAcceptedResponse":
        return cls(
            contract_version=1,
            finance_research_id=result.finance_research_id,
            request_id=result.request_id,
            source_domain=result.source_domain,
            source_reference=result.source_reference,
            instrument=result.instrument,
            recommendation=result.recommendation,
            confidence=result.confidence,
            issues=list(result.issues),
            correlation_id=result.correlation_id,
            created_at=result.created_at,
            replayed=result.replayed,
            status="accepted",
        )


class FinanceResearchQueuedResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_id: UUID
    request_id: UUID
    correlation_id: str
    status: Literal["queued"]

    @classmethod
    def from_result(
        cls, result: FinanceResearchQueuedResult
    ) -> "FinanceResearchQueuedResponse":
        return cls(
            job_id=result.job_id,
            request_id=result.request_id,
            correlation_id=result.correlation_id,
            status="queued",
        )


class ProblemDetails(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str
    title: str
    status: int
    detail: str
    code: str
    correlation_id: str


async def request_context(request: Request) -> RequestContext:
    provider = cast(RequestContextProvider | None, request.app.state.context_provider)
    if provider is None:
        raise AuthenticationRequiredError("Authentication is unavailable.")
    context = await provider.resolve(request)
    request.state.request_context = context
    return context


def handlers(request: Request) -> FinanceResearchHandlers:
    value = cast(FinanceResearchHandlers | None, request.app.state.finance_handlers)
    if value is None:
        raise ApiUnavailableError("Finance capability is unavailable.")
    return value


@router.post(
    "",
    operation_id="createFinanceResearch",
    response_model=FinanceResearchAcceptedResponse,
    responses={
        400: {"model": ProblemDetails},
        401: {"model": ProblemDetails},
        403: {"model": ProblemDetails},
        409: {"model": ProblemDetails},
        422: {"model": ProblemDetails},
        503: {"model": ProblemDetails},
    },
    status_code=status.HTTP_201_CREATED,
)
async def create_finance_research(
    body: CreateFinanceResearchRequest,
    context: Annotated[RequestContext, Depends(request_context)],
    finance_handlers: Annotated[FinanceResearchHandlers, Depends(handlers)],
    idempotency_key: Annotated[
        str,
        Header(alias="Idempotency-Key", min_length=1, max_length=200),
    ],
) -> FinanceResearchAcceptedResponse:
    result = await finance_handlers.create.execute(
        body.to_command(idempotency_key), context
    )
    return FinanceResearchAcceptedResponse.from_result(result)


@router.post(
    "/jobs",
    operation_id="enqueueFinanceResearch",
    response_model=FinanceResearchQueuedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def enqueue_finance_research(
    body: CreateFinanceResearchRequest,
    context: Annotated[RequestContext, Depends(request_context)],
    finance_handlers: Annotated[FinanceResearchHandlers, Depends(handlers)],
    idempotency_key: Annotated[
        str,
        Header(alias="Idempotency-Key", min_length=1, max_length=200),
    ],
) -> FinanceResearchQueuedResponse:
    if finance_handlers.enqueue is None:
        raise ApiUnavailableError("Finance job queue is unavailable.")
    result = await finance_handlers.enqueue.execute(
        body.to_command(idempotency_key), context
    )
    return FinanceResearchQueuedResponse.from_result(result)


@router.get("/livez", include_in_schema=False)
async def livez() -> dict[str, str]:
    return {"status": "alive"}


@router.get("/readyz", include_in_schema=False)
async def readyz() -> dict[str, str]:
    return {"status": "ready"}
