import pytest
from finance_agents import AgentAssessment, FinanceAgentRole


def test_agent_assessment_preserves_role_and_evidence() -> None:
    assessment = AgentAssessment(
        role=FinanceAgentRole.FUNDAMENTAL,
        stance="bullish",
        confidence=0.8,
        rationale="Cash generation supports the thesis.",
        evidence_references=("sec:10q:2026-q2",),
    )

    assert assessment.role is FinanceAgentRole.FUNDAMENTAL
    assert assessment.evidence_references == ("sec:10q:2026-q2",)


def test_agent_assessment_rejects_invalid_confidence() -> None:
    with pytest.raises(ValueError, match="between 0 and 1"):
        AgentAssessment(
            role=FinanceAgentRole.RISK,
            stance="neutral",
            confidence=1.1,
            rationale="Needs review.",
        )
