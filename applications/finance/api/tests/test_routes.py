from uuid import UUID

from fastapi.testclient import TestClient
from finance_api import create_app
from finance_persistence import InMemoryFinanceUnitOfWorkFactory


def test_finance_research_route_creates_result() -> None:
    factory = InMemoryFinanceUnitOfWorkFactory()
    factory.grant_permission(
        actor_id=UUID("30000000-0000-0000-0000-000000000001"),
        tenant_id=UUID("30000000-0000-0000-0000-000000000002"),
        permission="finance.research.create",
    )
    client = TestClient(create_app(uow_factory=factory))
    payload = {
        "contract_version": 1,
        "request_id": "30000000-0000-0000-0000-000000000010",
        "source_domain": "finance",
        "source_reference": "portfolio-ops/weekly-research",
        "instrument": "AAPL",
        "objective": (
            "Evaluate whether Apple stock is suitable for a medium-term long position."
        ),
        "thesis": "Services growth and capital returns support upside.",
        "horizon_days": 90,
        "domain_context": {
            "as_of": "2026-08-13T15:00:00Z",
            "sentiment": "positive",
        },
        "research": [
            {
                "summary": "Recent earnings showed resilient margin performance.",
                "facts": ["Gross margin held above 45%"],
            }
        ],
        "sources": [
            {
                "source_reference": "sec-10q-aapl-2026q2",
                "title": "Apple 10-Q Q2 2026",
                "url": "https://www.sec.gov",
                "as_of": "2026-08-13T15:00:00Z",
            }
        ],
        "constraints": ["paper-trading only", "do not execute live orders"],
        "quality_metadata": {"review_status": "finance-reviewed"},
    }
    response = client.post(
        "/v1/finance-researches",
        headers={
            "Idempotency-Key": "abc123",
            "X-Actor-Id": "30000000-0000-0000-0000-000000000001",
            "X-Tenant-Id": "30000000-0000-0000-0000-000000000002",
            "X-Correlation-Id": "corr-30000000-0000-0000-0000-000000000003",
        },
        json=payload,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "accepted"
    assert body["source_domain"] == "finance"
    assert body["instrument"] == "AAPL"

    replay = client.post(
        "/v1/finance-researches",
        headers={
            "Idempotency-Key": "abc123",
            "X-Actor-Id": "30000000-0000-0000-0000-000000000001",
            "X-Tenant-Id": "30000000-0000-0000-0000-000000000002",
            "X-Correlation-Id": "corr-30000000-0000-0000-0000-000000000003",
        },
        json=payload,
    )

    assert replay.status_code == 201
    assert replay.json()["finance_research_id"] == body["finance_research_id"]


def test_finance_research_job_route_enqueues_durable_work() -> None:
    actor_id = UUID("30000000-0000-0000-0000-000000000001")
    tenant_id = UUID("30000000-0000-0000-0000-000000000002")
    factory = InMemoryFinanceUnitOfWorkFactory(
        memberships={(actor_id, tenant_id): {"finance.research.create"}}
    )
    client = TestClient(create_app(uow_factory=factory))
    response = client.post(
        "/v1/finance-researches/jobs",
        headers={
            "Idempotency-Key": "async-abc123",
            "X-Actor-Id": str(actor_id),
            "X-Tenant-Id": str(tenant_id),
            "X-Correlation-Id": "corr-async",
        },
        json={
            "contract_version": 1,
            "request_id": "30000000-0000-0000-0000-000000000012",
            "source_domain": "finance",
            "source_reference": "async-test",
            "instrument": "AAPL",
            "objective": "Evaluate the instrument.",
            "domain_context": {"as_of": "2026-08-13T15:00:00Z"},
        },
    )

    assert response.status_code == 202
    assert response.json()["status"] == "queued"
    assert factory.state.jobs[0].request_id == UUID(
        "30000000-0000-0000-0000-000000000012"
    )
