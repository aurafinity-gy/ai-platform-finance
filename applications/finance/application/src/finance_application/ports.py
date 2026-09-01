from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, Self
from uuid import UUID

from finance_domain import JsonValue


@dataclass(frozen=True, slots=True)
class RequestContext:
    actor_id: UUID
    tenant_id: UUID
    correlation_id: str


class Clock(Protocol):
    def now(self) -> datetime: ...


class IdGenerator(Protocol):
    def new_uuid(self) -> UUID: ...


@dataclass(frozen=True, slots=True)
class CommandScope:
    tenant_id: UUID
    actor_id: UUID
    operation: str
    key_hash: str


@dataclass(frozen=True, slots=True)
class StoredCommandResult:
    scope: CommandScope
    fingerprint: str
    response_status: int
    result: dict[str, str]
    target_id: UUID
    correlation_id: str
    created_at: datetime
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class AuditEntry:
    entry_id: UUID
    context: RequestContext
    action: str
    target_type: str
    target_id: UUID
    result: str
    risk: str
    occurred_at: datetime
    metadata: dict[str, str]


@dataclass(frozen=True, slots=True)
class FinanceResearchRecord:
    finance_research_id: UUID
    tenant_id: UUID
    actor_id: UUID
    request_id: UUID
    source_domain: str
    source_reference: str
    instrument: str
    recommendation: str
    confidence: float
    issues: tuple[str, ...]
    correlation_id: str
    created_at: datetime
    replayed: bool
    status: str
    contract_version: int


@dataclass(frozen=True, slots=True)
class FinanceResearchJob:
    job_id: UUID
    tenant_id: UUID
    actor_id: UUID
    request_id: UUID
    payload: dict[str, JsonValue]
    attempts: int = 0


class FinanceResearchJobRepository(Protocol):
    async def enqueue(self, job: FinanceResearchJob) -> FinanceResearchJob: ...

    async def claim(self, *, worker_id: str) -> FinanceResearchJob | None: ...

    async def complete(self, *, job_id: UUID) -> None: ...

    async def fail(self, *, job_id: UUID, error: str, retry_at: datetime) -> None: ...


class MembershipRepository(Protocol):
    async def has_permission(
        self,
        *,
        actor_id: UUID,
        tenant_id: UUID,
        permission: str,
    ) -> bool: ...


class IdempotencyRepository(Protocol):
    async def lock_and_get(self, scope: CommandScope) -> StoredCommandResult | None: ...

    async def add(self, result: StoredCommandResult) -> None: ...


class AuditRepository(Protocol):
    async def add(self, entry: AuditEntry) -> None: ...


class FinanceResearchRepository(Protocol):
    async def add(self, record: FinanceResearchRecord) -> None: ...


class FinanceUnitOfWork(Protocol):
    researches: FinanceResearchRepository
    memberships: MembershipRepository
    idempotency: IdempotencyRepository
    audit: AuditRepository
    jobs: FinanceResearchJobRepository

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: object | None,
    ) -> None: ...


class FinanceUnitOfWorkFactory(Protocol):
    def create(self, context: RequestContext) -> FinanceUnitOfWork: ...
