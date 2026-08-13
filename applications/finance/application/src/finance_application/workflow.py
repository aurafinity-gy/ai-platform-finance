from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

from finance_domain import (
    FinanceResearchRequest,
    FinanceResearchResult,
    ResearchMaterial,
    SourceMaterial,
)

from finance_application.ports import RequestContext


@dataclass(frozen=True, slots=True)
class AnalystView:
    label: str
    stance: str
    confidence: float
    rationale: str


@dataclass(frozen=True, slots=True)
class DebateResult:
    bull_case: str
    bear_case: str
    recommendation: str
    confidence: float
    issues: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class FinanceResearchCommand:
    request_id: UUID
    source_domain: str
    source_reference: str
    instrument: str
    objective: str
    thesis: str | None
    horizon_days: int | None
    domain_context: dict[str, object]
    research: tuple[ResearchMaterial, ...]
    sources: tuple[SourceMaterial, ...]
    constraints: tuple[str, ...]
    quality_metadata: dict[str, object]
    contract_version: int = 1


class FinanceResearchWorkflow(Protocol):
    async def execute(
        self,
        command: FinanceResearchCommand,
        context: RequestContext,
        *,
        finance_research_id: UUID,
        created_at: datetime,
    ) -> FinanceResearchResult: ...


class DeterministicFinanceResearchWorkflow:
    async def execute(
        self,
        command: FinanceResearchCommand,
        context: RequestContext,
        *,
        finance_research_id: UUID,
        created_at: datetime,
    ) -> FinanceResearchResult:
        research = FinanceResearchRequest.create(
            research_id=finance_research_id,
            tenant_id=context.tenant_id,
            request_id=command.request_id,
            source_domain=command.source_domain,
            source_reference=command.source_reference,
            instrument=command.instrument,
            objective=command.objective,
            thesis=command.thesis,
            horizon_days=command.horizon_days,
            domain_context=command.domain_context,
            research=command.research,
            sources=command.sources,
            constraints=command.constraints,
            quality_metadata=command.quality_metadata,
            created_by=context.actor_id,
            created_at=created_at,
        )
        fundamental = self._fundamental_view(research)
        sentiment = self._sentiment_view(research)
        news = self._news_view(research)
        technical = self._technical_view(research)
        debate = self._debate(research, fundamental, sentiment, news, technical)
        return FinanceResearchResult.create(
            research_id=research.id,
            request_id=research.request_id,
            source_domain=research.source_domain,
            source_reference=research.source_reference,
            instrument=research.instrument,
            recommendation=debate.recommendation,
            confidence=debate.confidence,
            issues=debate.issues,
            correlation_id=context.correlation_id,
            replayed=False,
            created_at=created_at,
        )

    def _fundamental_view(self, research: FinanceResearchRequest) -> AnalystView:
        text = self._joined_text(research.research, research.objective, research.thesis)
        bullish = self._contains_any(text, ("growth", "margin", "buyback", "resilient"))
        stance = "bullish" if bullish else "neutral"
        confidence = 0.68 if bullish else 0.45
        rationale = (
            "Fundamental evidence points to durable cash generation."
            if bullish
            else "Fundamental evidence is mixed and requires more confirmation."
        )
        return AnalystView("fundamental", stance, confidence, rationale)

    def _sentiment_view(self, research: FinanceResearchRequest) -> AnalystView:
        sentiment_hint = str(research.domain_context.get("sentiment", "")).lower()
        bullish = sentiment_hint in {"positive", "constructive", "bullish"}
        stance = "bullish" if bullish else "neutral"
        confidence = 0.62 if bullish else 0.4
        rationale = (
            "Sentiment context is constructive."
            if bullish
            else "Sentiment context is neutral or unspecified."
        )
        return AnalystView("sentiment", stance, confidence, rationale)

    def _news_view(self, research: FinanceResearchRequest) -> AnalystView:
        bullish = bool(research.sources) and any(
            "sec" in source.source_reference.lower() or "10q" in source.title.lower()
            for source in research.sources
        )
        stance = "bullish" if bullish else "neutral"
        confidence = 0.58 if bullish else 0.38
        rationale = (
            "News and filings support an evidence-backed review."
            if bullish
            else "News coverage is not strong enough to change the thesis."
        )
        return AnalystView("news", stance, confidence, rationale)

    def _technical_view(self, research: FinanceResearchRequest) -> AnalystView:
        horizon_days = research.horizon_days or 0
        bullish = horizon_days >= 60
        stance = "bullish" if bullish else "neutral"
        confidence = 0.64 if bullish else 0.42
        rationale = (
            "Technical horizon favors a trend-following posture."
            if bullish
            else "Technical horizon is too short for strong trend conviction."
        )
        return AnalystView("technical", stance, confidence, rationale)

    def _debate(
        self,
        research: FinanceResearchRequest,
        fundamental: AnalystView,
        sentiment: AnalystView,
        news: AnalystView,
        technical: AnalystView,
    ) -> DebateResult:
        views = (fundamental, sentiment, news, technical)
        bullish_count = sum(1 for view in views if view.stance == "bullish")
        neutral_count = sum(1 for view in views if view.stance == "neutral")
        bull_case = self._bull_case(research, views)
        bear_case = (
            "Risk controls remain important while the desk stays paper-only."
            if neutral_count >= 1
            else "The bull case is strong but still needs a risk check."
        )
        if bullish_count >= 3:
            recommendation = "buy"
            confidence = 0.75
        elif bullish_count == 2:
            recommendation = "hold"
            confidence = 0.55
        else:
            recommendation = "sell"
            confidence = 0.35
        issues = self._issues(research, recommendation, bullish_count, neutral_count)
        return DebateResult(
            bull_case=bull_case,
            bear_case=bear_case,
            recommendation=recommendation,
            confidence=confidence,
            issues=issues,
        )

    def _bull_case(
        self, research: FinanceResearchRequest, views: tuple[AnalystView, ...]
    ) -> str:
        stance_summary = ", ".join(f"{view.label}:{view.stance}" for view in views)
        return (
            f"{research.instrument} has a constructive multi-view setup. "
            f"Desk views: {stance_summary}."
        )

    def _issues(
        self,
        research: FinanceResearchRequest,
        recommendation: str,
        bullish_count: int,
        neutral_count: int,
    ) -> tuple[str, ...]:
        issues: list[str] = []
        if not research.sources:
            issues.append("No source materials were supplied.")
        if recommendation == "sell":
            issues.append("Consensus is too weak for a long thesis.")
        if bullish_count < 2:
            issues.append("Fewer than two analyst views are bullish.")
        if neutral_count == len(research.research) and research.research:
            issues.append("Research materials are mostly neutral.")
        if "do not execute live orders" not in {
            constraint.lower() for constraint in research.constraints
        }:
            issues.append("Paper-trading guardrail was not explicit.")
        return tuple(issues)

    def _joined_text(
        self,
        research_items: tuple[ResearchMaterial, ...],
        objective: str,
        thesis: str | None,
    ) -> str:
        parts = [objective, thesis or ""]
        for item in research_items:
            parts.append(item.summary)
            parts.extend(item.facts)
        return " ".join(parts).lower()

    def _contains_any(self, text: str, words: tuple[str, ...]) -> bool:
        return any(word in text for word in words)
