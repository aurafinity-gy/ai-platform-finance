from datetime import UTC, datetime
from uuid import UUID

import pytest

from finance_domain import (
    FinanceResearchRequest,
    FinanceResearchResult,
    InvalidFinanceResearchError,
    ResearchMaterial,
    SourceMaterial,
)


def test_finance_research_request_normalizes_core_fields() -> None:
    request = FinanceResearchRequest.create(
        research_id=UUID("30000000-0000-0000-0000-000000000010"),
        tenant_id=UUID("30000000-0000-0000-0000-000000000011"),
        request_id=UUID("30000000-0000-0000-0000-000000000012"),
        source_domain=" Finance ",
        source_reference="portfolio/research",
        instrument="aapl",
        objective="Assess medium-term upside.",
        thesis="Services growth supports the long thesis.",
        horizon_days=90,
        domain_context={"as_of": "2026-08-13T15:00:00Z"},
        research=(
            ResearchMaterial.create(
                "Bullish fundamentals remain intact.",
                ("Margins are resilient.",),
            ),
        ),
        sources=(
            SourceMaterial.create(
                source_reference="sec-10q",
                title="Apple 10-Q",
                url="https://www.sec.gov",
                as_of=datetime(2026, 8, 13, 15, 0, tzinfo=UTC),
            ),
        ),
        constraints=("paper-trading only",),
        quality_metadata={"review_status": "finance-reviewed"},
        created_by=UUID("30000000-0000-0000-0000-000000000013"),
        created_at=datetime(2026, 8, 13, 15, 0, tzinfo=UTC),
    )

    assert request.source_domain == "finance"
    assert request.instrument == "AAPL"
    assert request.created_at.tzinfo is UTC


def test_finance_research_result_enforces_confidence_bounds() -> None:
    result = FinanceResearchResult.create(
        research_id=UUID("30000000-0000-0000-0000-000000000020"),
        request_id=UUID("30000000-0000-0000-0000-000000000021"),
        source_domain="finance",
        source_reference="portfolio/research",
        instrument="AAPL",
        recommendation="buy",
        confidence=0.75,
        issues=(),
        correlation_id="corr-30000000-0000-0000-0000-000000000022",
        replayed=False,
        created_at=datetime(2026, 8, 13, 15, 5, tzinfo=UTC),
    )

    assert result.status.value == "accepted"
    assert result.instrument == "AAPL"


def test_finance_research_request_rejects_non_utc_time() -> None:
    with pytest.raises(InvalidFinanceResearchError):
        FinanceResearchRequest.create(
            research_id=UUID("30000000-0000-0000-0000-000000000030"),
            tenant_id=UUID("30000000-0000-0000-0000-000000000031"),
            request_id=UUID("30000000-0000-0000-0000-000000000032"),
            source_domain="finance",
            source_reference="portfolio/research",
            instrument="AAPL",
            objective="Assess medium-term upside.",
            thesis=None,
            horizon_days=90,
            domain_context={"as_of": "2026-08-13T15:00:00Z"},
            research=(),
            sources=(),
            constraints=(),
            quality_metadata={},
            created_by=UUID("30000000-0000-0000-0000-000000000033"),
            created_at=datetime(2026, 8, 13, 15, 0),
        )

