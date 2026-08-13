from uuid import UUID

from finance_api_service import RuntimeSettings, create_runtime_app
from finance_application import RequestContext


def test_finance_runtime_app_builds() -> None:
    class FakeContextProvider:
        async def resolve(self, request):  # type: ignore[no-untyped-def]
            return RequestContext(
                actor_id=UUID("30000000-0000-0000-0000-000000000001"),
                tenant_id=UUID("30000000-0000-0000-0000-000000000002"),
                correlation_id="corr-30000000-0000-0000-0000-000000000003",
            )

    class FakeUnitOfWorkFactory:
        def create(self, context):  # type: ignore[no-untyped-def]
            return object()

    app = create_runtime_app(
        settings=RuntimeSettings(
            database_url="postgresql://finance:test@localhost:5432/finance",
            auth_jwks_url="https://auth.test.local/jwks",
            auth_issuer="https://auth.test.local",
            auth_audience="authenticated",
        ),
        uow_factory=FakeUnitOfWorkFactory(),
        context_provider=FakeContextProvider(),
    )

    assert app.title == "AI Platform Finance API"
