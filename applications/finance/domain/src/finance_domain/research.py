import re
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from urllib.parse import urlparse
from uuid import UUID
from typing import TypeAlias

JsonScalar: TypeAlias = str | int | float | bool | None
JsonValue: TypeAlias = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]

_SOURCE_DOMAIN = re.compile(r"^[a-z][a-z0-9.-]{0,63}$")
_INSTRUMENT = re.compile(r"^[A-Z0-9][A-Z0-9.-]{0,19}$")


class InvalidFinanceResearchError(ValueError):
    """Raised when Finance research input violates an invariant."""


@dataclass(frozen=True, slots=True)
class ResearchMaterial:
    summary: str
    facts: tuple[str, ...]

    @classmethod
    def create(cls, summary: str, facts: tuple[str, ...]) -> "ResearchMaterial":
        return cls(
            summary=_required_text("research summary", summary, 2_000),
            facts=tuple(_required_text("research fact", fact, 1_000) for fact in facts),
        )


@dataclass(frozen=True, slots=True)
class SourceMaterial:
    source_reference: str
    title: str
    url: str | None = None
    as_of: datetime | None = None

    @classmethod
    def create(
        cls,
        *,
        source_reference: str,
        title: str,
        url: str | None,
        as_of: datetime | None,
    ) -> "SourceMaterial":
        normalized_url = url.strip() if url else None
        if normalized_url:
            parsed = urlparse(normalized_url)
            if parsed.scheme != "https" or not parsed.netloc:
                raise InvalidFinanceResearchError("Source URLs must use HTTPS.")
        normalized_as_of = None
        if as_of is not None:
            if as_of.tzinfo is None or as_of.utcoffset() is None:
                raise InvalidFinanceResearchError(
                    "Source as-of time must be timezone-aware."
                )
            normalized_as_of = as_of.astimezone(UTC)
        return cls(
            source_reference=_required_text(
                "source material reference", source_reference, 500
            ),
            title=_required_text("source material title", title, 300),
            url=normalized_url,
            as_of=normalized_as_of,
        )


class FinanceResearchStatus(StrEnum):
    ACCEPTED = "accepted"


@dataclass(frozen=True, slots=True)
class FinanceResearchRequest:
    id: UUID
    tenant_id: UUID
    request_id: UUID
    source_domain: str
    source_reference: str
    instrument: str
    objective: str
    thesis: str | None
    horizon_days: int | None
    domain_context: dict[str, JsonValue]
    research: tuple[ResearchMaterial, ...]
    sources: tuple[SourceMaterial, ...]
    constraints: tuple[str, ...]
    quality_metadata: dict[str, JsonValue]
    created_by: UUID
    created_at: datetime
    contract_version: int = 1

    @classmethod
    def create(
        cls,
        *,
        research_id: UUID,
        tenant_id: UUID,
        request_id: UUID,
        source_domain: str,
        source_reference: str,
        instrument: str,
        objective: str,
        thesis: str | None,
        horizon_days: int | None,
        domain_context: dict[str, JsonValue],
        research: tuple[ResearchMaterial, ...],
        sources: tuple[SourceMaterial, ...],
        constraints: tuple[str, ...],
        quality_metadata: dict[str, JsonValue],
        created_by: UUID,
        created_at: datetime,
    ) -> "FinanceResearchRequest":
        if created_at.tzinfo is None or created_at.utcoffset() is None:
            raise InvalidFinanceResearchError(
                "Research request time must be timezone-aware."
            )

        normalized_domain = source_domain.strip().lower()
        if normalized_domain != "finance" or not _SOURCE_DOMAIN.fullmatch(
            normalized_domain
        ):
            raise InvalidFinanceResearchError("Source domain must be finance.")

        normalized_instrument = instrument.strip().upper()
        if not _INSTRUMENT.fullmatch(normalized_instrument):
            raise InvalidFinanceResearchError("Instrument symbol is invalid.")

        if not domain_context:
            raise InvalidFinanceResearchError("Domain context is required.")
        if horizon_days is not None and horizon_days <= 0:
            raise InvalidFinanceResearchError("Horizon days must be positive.")
        if len(constraints) > 100:
            raise InvalidFinanceResearchError("At most 100 constraints may be used.")

        return cls(
            id=research_id,
            tenant_id=tenant_id,
            request_id=request_id,
            source_domain=normalized_domain,
            source_reference=_required_text(
                "source reference", source_reference, 500
            ),
            instrument=normalized_instrument,
            objective=_required_text("objective", objective, 1_000),
            thesis=_optional_text("thesis", thesis, 1_000),
            horizon_days=horizon_days,
            domain_context=dict(domain_context),
            research=research,
            sources=sources,
            constraints=tuple(
                _required_text("constraint", item, 500) for item in constraints
            ),
            quality_metadata=dict(quality_metadata),
            created_by=created_by,
            created_at=created_at.astimezone(UTC),
        )


@dataclass(frozen=True, slots=True)
class FinanceResearchResult:
    id: UUID
    request_id: UUID
    source_domain: str
    source_reference: str
    instrument: str
    recommendation: str
    confidence: float
    issues: tuple[str, ...]
    correlation_id: str
    replayed: bool
    created_at: datetime
    status: FinanceResearchStatus = FinanceResearchStatus.ACCEPTED
    contract_version: int = 1

    @classmethod
    def create(
        cls,
        *,
        research_id: UUID,
        request_id: UUID,
        source_domain: str,
        source_reference: str,
        instrument: str,
        recommendation: str,
        confidence: float,
        issues: tuple[str, ...],
        correlation_id: str,
        replayed: bool,
        created_at: datetime,
    ) -> "FinanceResearchResult":
        if created_at.tzinfo is None or created_at.utcoffset() is None:
            raise InvalidFinanceResearchError(
                "Result time must be timezone-aware."
            )
        normalized_domain = source_domain.strip().lower()
        if normalized_domain != "finance" or not _SOURCE_DOMAIN.fullmatch(
            normalized_domain
        ):
            raise InvalidFinanceResearchError("Source domain must be finance.")
        normalized_instrument = instrument.strip().upper()
        if not _INSTRUMENT.fullmatch(normalized_instrument):
            raise InvalidFinanceResearchError("Instrument symbol is invalid.")
        normalized_recommendation = recommendation.strip().lower()
        if not normalized_recommendation:
            raise InvalidFinanceResearchError("Recommendation is required.")
        if not 0.0 <= confidence <= 1.0:
            raise InvalidFinanceResearchError("Confidence must be between 0 and 1.")
        return cls(
            id=research_id,
            request_id=request_id,
            source_domain=normalized_domain,
            source_reference=_required_text(
                "source reference", source_reference, 500
            ),
            instrument=normalized_instrument,
            recommendation=normalized_recommendation,
            confidence=confidence,
            issues=tuple(_required_text("issue", item, 500) for item in issues),
            correlation_id=_required_text("correlation id", correlation_id, 200),
            replayed=replayed,
            created_at=created_at.astimezone(UTC),
        )


def _required_text(label: str, value: str, maximum: int) -> str:
    normalized = value.strip()
    if not normalized or len(normalized) > maximum:
        raise InvalidFinanceResearchError(
            f"{label.capitalize()} must contain between 1 and {maximum} characters."
        )
    return normalized


def _optional_text(label: str, value: str | None, maximum: int) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    if not normalized or len(normalized) > maximum:
        raise InvalidFinanceResearchError(
            f"{label.capitalize()} must contain between 1 and {maximum} characters."
        )
    return normalized
