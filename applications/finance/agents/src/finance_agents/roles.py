from dataclasses import dataclass
from enum import StrEnum


class FinanceAgentRole(StrEnum):
    FUNDAMENTAL = "fundamental"
    SENTIMENT = "sentiment"
    NEWS = "news"
    TECHNICAL = "technical"
    BULL_DEBATE = "bull_debate"
    BEAR_DEBATE = "bear_debate"
    TRADER = "trader"
    RISK = "risk"
    PORTFOLIO = "portfolio"


@dataclass(frozen=True, slots=True)
class AgentAssessment:
    role: FinanceAgentRole
    stance: str
    confidence: float
    rationale: str
    evidence_references: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Agent confidence must be between 0 and 1.")
        if not self.rationale.strip():
            raise ValueError("Agent rationale is required.")
