import json
from typing import Any
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
from finance_application.ports import (
    AuditRepository,
    FinanceResearchRepository,
    IdempotencyRepository,
    MembershipRepository,
)
from psycopg import AsyncConnection
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from psycopg_pool import AsyncConnectionPool


class PostgresFinanceResearchRepository:
    def __init__(self, connection: AsyncConnection[Any]) -> None:
        self._connection = connection

    async def add(self, record: FinanceResearchRecord) -> None:
        await self._connection.execute(
            """
            insert into finance.research_records (
                id, tenant_id, actor_id, request_id, source_domain,
                source_reference, instrument, recommendation, confidence,
                issues, correlation_id, created_at, replayed, status,
                contract_version
            ) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                record.finance_research_id,
                record.tenant_id,
                record.actor_id,
                record.request_id,
                record.source_domain,
                record.source_reference,
                record.instrument,
                record.recommendation,
                record.confidence,
                list(record.issues),
                record.correlation_id,
                record.created_at,
                record.replayed,
                record.status,
                record.contract_version,
            ),
        )


class PostgresFinanceMembershipRepository:
    def __init__(self, connection: AsyncConnection[Any]) -> None:
        self._connection = connection

    async def has_permission(
        self,
        *,
        actor_id: UUID,
        tenant_id: UUID,
        permission: str,
    ) -> bool:
        cursor = await self._connection.execute(
            """
            select 1
            from platform.memberships
            where actor_id = %s and tenant_id = %s and active
              and %s = any(permissions)
            """,
            (actor_id, tenant_id, permission),
        )
        return await cursor.fetchone() is not None


class PostgresFinanceIdempotencyRepository:
    def __init__(self, connection: AsyncConnection[Any]) -> None:
        self._connection = connection

    async def lock_and_get(self, scope: CommandScope) -> StoredCommandResult | None:
        lock_value = (
            f"{scope.tenant_id}:{scope.actor_id}:{scope.operation}:{scope.key_hash}"
        )
        await self._connection.execute(
            "select pg_advisory_xact_lock(hashtextextended(%s, 0))",
            (lock_value,),
        )
        cursor = await self._connection.execute(
            """
            select fingerprint, response_status, result, target_id,
                   correlation_id, created_at, expires_at
            from finance.command_idempotency
            where tenant_id = %s and actor_id = %s
              and operation = %s and key_hash = %s
            """,
            (
                scope.tenant_id,
                scope.actor_id,
                scope.operation,
                scope.key_hash,
            ),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return StoredCommandResult(
            scope=scope,
            fingerprint=row["fingerprint"],
            response_status=row["response_status"],
            result=row["result"],
            target_id=row["target_id"],
            correlation_id=row["correlation_id"],
            created_at=row["created_at"],
            expires_at=row["expires_at"],
        )

    async def add(self, result: StoredCommandResult) -> None:
        await self._connection.execute(
            """
            insert into finance.command_idempotency (
                tenant_id, actor_id, operation, key_hash, fingerprint,
                response_status, result, target_id, correlation_id,
                created_at, expires_at
            ) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                result.scope.tenant_id,
                result.scope.actor_id,
                result.scope.operation,
                result.scope.key_hash,
                result.fingerprint,
                result.response_status,
                Jsonb(result.result),
                result.target_id,
                result.correlation_id,
                result.created_at,
                result.expires_at,
            ),
        )


class PostgresFinanceAuditRepository:
    def __init__(self, connection: AsyncConnection[Any]) -> None:
        self._connection = connection

    async def add(self, entry: AuditEntry) -> None:
        await self._connection.execute(
            """
            insert into platform.audit_entries (
                id, tenant_id, actor_id, action, target_type, target_id,
                result, risk, occurred_at, metadata, correlation_id
            ) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                entry.entry_id,
                entry.context.tenant_id,
                entry.context.actor_id,
                entry.action,
                entry.target_type,
                entry.target_id,
                entry.result,
                entry.risk,
                entry.occurred_at,
                Jsonb(entry.metadata),
                entry.context.correlation_id,
            ),
        )


class PostgresFinanceUnitOfWork:
    researches: FinanceResearchRepository
    memberships: MembershipRepository
    idempotency: IdempotencyRepository
    audit: AuditRepository

    def __init__(
        self,
        pool: AsyncConnectionPool[Any],
        context: RequestContext,
    ) -> None:
        self._pool = pool
        self._context = context
        self._connection: AsyncConnection[Any] | None = None
        self._previous_row_factory: Any = None

    async def __aenter__(self) -> "PostgresFinanceUnitOfWork":
        connection = await self._pool.getconn()
        self._connection = connection
        self._previous_row_factory = connection.row_factory
        connection.row_factory = dict_row
        try:
            await connection.execute("begin")
            await connection.execute("set local role authenticated")
            claims = json.dumps(
                {
                    "sub": str(self._context.actor_id),
                    "tenant_id": str(self._context.tenant_id),
                    "role": "authenticated",
                }
            )
            await connection.execute(
                "select set_config('request.jwt.claims', %s, true)",
                (claims,),
            )
        except BaseException:
            await connection.rollback()
            await self._reset_and_return(connection)
            raise
        self.researches = PostgresFinanceResearchRepository(connection)
        self.memberships = PostgresFinanceMembershipRepository(connection)
        self.idempotency = PostgresFinanceIdempotencyRepository(connection)
        self.audit = PostgresFinanceAuditRepository(connection)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: object | None,
    ) -> None:
        connection = self._required_connection()
        try:
            if exc_type is None:
                await connection.commit()
            else:
                await connection.rollback()
        finally:
            await self._reset_and_return(connection)

    def _required_connection(self) -> AsyncConnection[Any]:
        if self._connection is None:
            raise RuntimeError("Unit of work has not been entered.")
        return self._connection

    async def _reset_and_return(self, connection: AsyncConnection[Any]) -> None:
        try:
            await connection.rollback()
            await connection.execute("reset role")
            await connection.execute("reset all")
        finally:
            connection.row_factory = self._previous_row_factory
            self._previous_row_factory = None
            self._connection = None
            await self._pool.putconn(connection)


class PostgresFinanceUnitOfWorkFactory:
    def __init__(self, pool: AsyncConnectionPool[Any]) -> None:
        self._pool = pool

    def create(self, context: RequestContext) -> FinanceUnitOfWork:
        return PostgresFinanceUnitOfWork(self._pool, context)

