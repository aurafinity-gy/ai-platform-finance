from fastapi import Request
from fastapi.testclient import TestClient
from finance_api import AuthenticationRequiredError, create_app


class MissingAuthenticationProvider:
    async def resolve(self, _: Request) -> object:
        raise AuthenticationRequiredError("bearer_token_required")


def test_finance_api_app_builds() -> None:
    app = create_app()

    assert app.title == "AI Platform Finance API"


def test_missing_authentication_returns_401_problem_details() -> None:
    client = TestClient(create_app(context_provider=MissingAuthenticationProvider()))

    response = client.get(
        "/v1/finance-researches/jobs/30000000-0000-0000-0000-000000000001",
        headers={"X-Correlation-ID": "auth-test"},
    )

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.json()["code"] == "authentication_required"
    assert response.json()["correlation_id"] == "auth-test"

