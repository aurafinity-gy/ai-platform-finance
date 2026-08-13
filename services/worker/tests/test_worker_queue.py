from asyncio import run
from uuid import UUID

from finance_application import CreateFinanceResearch
from finance_worker import create_runtime_worker


def test_finance_worker_processes_queued_job() -> None:
    worker = create_runtime_worker()
    command = CreateFinanceResearch(
        request_id=UUID("30000000-0000-0000-0000-000000000010"),
        source_domain="finance",
        source_reference="portfolio-ops/weekly-research",
        instrument="AAPL",
        objective="Evaluate whether Apple stock is suitable for a medium-term long position.",
        thesis="Services growth and capital returns support upside.",
        horizon_days=90,
        domain_context={
            "as_of": "2026-08-13T15:00:00Z",
            "sentiment": "positive",
        },
        research=(),
        sources=(),
        constraints=("paper-trading only", "do not execute live orders"),
        quality_metadata={"review_status": "finance-reviewed"},
        idempotency_key="abc123",
    )

    async def exercise() -> None:
        await worker.submit(command)
        processed = await worker.process_one()
        assert processed

    run(exercise())
    assert worker.results
    assert worker.results[0]["status"] == "accepted"
