from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from finance_api import create_app
from finance_persistence import PostgresFinanceUnitOfWorkFactory
from psycopg_pool import AsyncConnectionPool

from finance_api_service.auth import (
    HttpJwkProvider,
    JwtRequestContextProvider,
    JwtVerifier,
)
from finance_api_service.settings import RuntimeSettings


def create_runtime_app(
    *,
    settings: RuntimeSettings | None = None,
    uow_factory: PostgresFinanceUnitOfWorkFactory | None = None,
    context_provider: JwtRequestContextProvider | None = None,
) -> FastAPI:
    pool: AsyncConnectionPool[object] | None = None
    factory = uow_factory
    provider = context_provider
    if factory is None or provider is None:
        runtime = settings or RuntimeSettings.from_environment()
        pool = AsyncConnectionPool(
            runtime.database_url,
            min_size=1,
            max_size=10,
            open=False,
        )
        factory = factory or PostgresFinanceUnitOfWorkFactory(pool)
        provider = provider or JwtRequestContextProvider(
            JwtVerifier(
                provider=HttpJwkProvider(runtime.auth_jwks_url),
                issuer=runtime.auth_issuer,
                audience=runtime.auth_audience,
            )
        )

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        if pool is None:
            yield
            return
        await pool.open()
        try:
            yield
        finally:
            await pool.close()

    app = create_app(
        uow_factory=factory,
        context_provider=provider,
        lifespan=lifespan,
    )
    if pool is not None:
        app.state.database_pool = pool

    @app.get("/livez", include_in_schema=False)
    async def livez() -> dict[str, str]:
        return {"status": "alive"}

    @app.get("/readyz", include_in_schema=False, response_model=None)
    async def readyz() -> dict[str, str]:
        if pool is None:
            return {"status": "ready"}
        try:
            async with pool.connection() as connection:
                await connection.execute("select 1")
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Finance database is unavailable.",
            ) from None
        return {"status": "ready"}

    return app
