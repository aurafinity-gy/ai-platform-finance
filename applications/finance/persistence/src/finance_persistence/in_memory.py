from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from finance_application import (
    AuditEntry,
    CommandScope,
    FinanceResearchRecord,
    FinanceUnitOfWork,
    FinanceUnitOfWorkFactory,
    RequestContext,
    StoredCommandResult,
)


@dataclass(slots=True)
class InMemoryFinanceState:
    memberships: dict[tuple[UUID, UUID], set[str]] = field(default_factory=dict)
    idempotency: dict[tuple[UUID, UUID, str, str], StoredCommandResult] = field(
        default_factory=dict
    )
    research_records: list[FinanceResearchRecord] = field(default_factory=list)
    audit_entries: list[AuditEntry] = field(default_factory=list)


class InMemoryFinanceMembershipRepository:
    def __init__(self, state: InMemoryFinanceState) -> None:
        self._state = state

    async def has_permission(
        self,
        *,
        actor_id: UUID,
        tenant_id: UUID,
        permission: str,
    ) -> bool:
        permissions = self._state.memberships.get((actor_id, tenant_id))
        return permissions is not None and permission in permissions


class InMemoryFinanceIdempotencyRepository:
    def __init__(self, state: InMemoryFinanceState) -> None:
        self._state = state

    async def lock_and_get(self, scope: CommandScope) -> StoredCommandResult | None:
        key = (scope.tenant_id, scope.actor_id, scope.operation, scope.key_hash)
        return self._state.idempotency.get(key)

    async def add(self, result: StoredCommandResult) -> None:
        key = (
            result.scope.tenant_id,
            result.scope.actor_id,
            result.scope.operation,
            result.scope.key_hash,
        )
        self._state.idempotency[key] = result


class InMemoryFinanceAuditRepository:
    def __init__(self, state: InMemoryFinanceState) -> None:
        self._state = state

    async def add(self, entry: AuditEntry) -> None:
        self._state.audit_entries.append(entry)


class InMemoryFinanceResearchRepository:
    def __init__(self, state: InMemoryFinanceState) -> None:
        self._state = state

    async def add(self, record: FinanceResearchRecord) -> None:
        self._state.research_records.append(record)


class InMemoryFinanceUnitOfWork:
    researches: InMemoryFinanceResearchRepository
    memberships: InMemoryFinanceMembershipRepository
    idempotency: InMemoryFinanceIdempotencyRepository
    audit: InMemoryFinanceAuditRepository

    def __init__(self, state: InMemoryFinanceState, context: RequestContext) -> None:
        self._state = state
        self._context = context
        self.researches = InMemoryFinanceResearchRepository(state)
        self.memberships = InMemoryFinanceMembershipRepository(state)
        self.idempotency = InMemoryFinanceIdempotencyRepository(state)
        self.audit = InMemoryFinanceAuditRepository(state)

    async def __aenter__(self) -> "InMemoryFinanceUnitOfWork":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: object | None,
    ) -> None:
        del exc_type, exc, traceback


class InMemoryFinanceUnitOfWorkFactory:
    def __init__(
        self,
        *,
        memberships: dict[tuple[UUID, UUID], set[str]] | None = None,
        state: InMemoryFinanceState | None = None,
    ) -> None:
        self.state = state or InMemoryFinanceState()
        if memberships:
            self.state.memberships.update(memberships)

    def grant_permission(
        self,
        *,
        actor_id: UUID,
        tenant_id: UUID,
        permission: str,
    ) -> None:
        self.state.memberships.setdefault((actor_id, tenant_id), set()).add(permission)

    def create(self, context: RequestContext) -> FinanceUnitOfWork:
        return InMemoryFinanceUnitOfWork(self.state, context)
