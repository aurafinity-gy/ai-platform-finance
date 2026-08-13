import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID

from finance_application.errors import (
    IdempotencyConflictError,
    InvalidIdempotencyKeyError,
    PermissionDeniedError,
)
from finance_application.ports import (
    AuditEntry,
    Clock,
    CommandScope,
    FinanceUnitOfWorkFactory,
    FinanceResearchRecord,
    IdGenerator,
    RequestContext,
    StoredCommandResult,
)
from finance_application.workflow import (
    DeterministicFinanceResearchWorkflow,
    FinanceResearchCommand,
    FinanceResearchWorkflow,
)
from finance_domain import FinanceResearchResult, JsonValue, ResearchMaterial, SourceMaterial

FINANCE_RESEARCH_CREATE_PERMISSION = "finance.research.create"
_OPERATION = "finance.research.create"
_REPLAY_WINDOW = timedelta(hours=24)


@dataclass(frozen=True, slots=True)
class CreateFinanceResearch:
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
    idempotency_key: str
    contract_version: int = 1


@dataclass(frozen=True, slots=True)
class FinanceResearchAcceptedResult:
    finance_research_id: UUID
    request_id: UUID
    source_domain: str
    source_reference: str
    instrument: str
    recommendation: str
    confidence: float
    issues: tuple[str, ...]
    correlation_id: str
    created_at: datetime
    replayed: bool = False
    status: str = "accepted"
    contract_version: int = 1

    def stored(self) -> dict[str, str]:
        return {
            "finance_research_id": str(self.finance_research_id),
            "request_id": str(self.request_id),
            "source_domain": self.source_domain,
            "source_reference": self.source_reference,
            "instrument": self.instrument,
            "recommendation": self.recommendation,
            "confidence": f"{self.confidence:.6f}",
            "correlation_id": self.correlation_id,
            "created_at": self.created_at.isoformat(),
            "contract_version": str(self.contract_version),
            "status": self.status,
            "issues": json.dumps(list(self.issues), separators=(",", ":")),
            "replayed": "true" if self.replayed else "false",
        }

    @classmethod
    def from_domain(
        cls, result: FinanceResearchResult
    ) -> "FinanceResearchAcceptedResult":
        return cls(
            finance_research_id=result.id,
            request_id=result.request_id,
            source_domain=result.source_domain,
            source_reference=result.source_reference,
            instrument=result.instrument,
            recommendation=result.recommendation,
            confidence=result.confidence,
            issues=result.issues,
            correlation_id=result.correlation_id,
            created_at=result.created_at,
            replayed=result.replayed,
            status=result.status.value,
            contract_version=result.contract_version,
        )


class CreateFinanceResearchHandler:
    def __init__(
        self,
        *,
        workflow: FinanceResearchWorkflow | None = None,
        clock: Clock,
        id_generator: IdGenerator,
        uow_factory: FinanceUnitOfWorkFactory | None = None,
    ) -> None:
        self._workflow = workflow or DeterministicFinanceResearchWorkflow()
        self._clock = clock
        self._id_generator = id_generator
        self._uow_factory = uow_factory

    async def execute(
        self, command: CreateFinanceResearch, context: RequestContext
    ) -> FinanceResearchAcceptedResult:
        if command.contract_version != 1:
            raise ValueError("Unsupported Finance research contract version.")
        scope = _command_scope(context, command.idempotency_key)
        fingerprint = _fingerprint(command)
        created_at = self._clock.now()
        finance_research_id = self._id_generator.new_uuid()
        if self._uow_factory is None:
            result = await self._workflow.execute(
                FinanceResearchCommand(
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
                    contract_version=command.contract_version,
                ),
                context,
                finance_research_id=finance_research_id,
                created_at=created_at,
            )
            return FinanceResearchAcceptedResult.from_domain(result)

        async with self._uow_factory.create(context) as uow:
            if not await uow.memberships.has_permission(
                actor_id=context.actor_id,
                tenant_id=context.tenant_id,
                permission=FINANCE_RESEARCH_CREATE_PERMISSION,
            ):
                raise PermissionDeniedError("Finance research creation is not allowed.")
            stored = await uow.idempotency.lock_and_get(scope)
            if stored is not None:
                if stored.fingerprint != fingerprint:
                    raise IdempotencyConflictError(
                        "The idempotency key has different input."
                    )
                return _replay_result(stored, context.correlation_id)

            result = await self._workflow.execute(
                FinanceResearchCommand(
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
                    contract_version=command.contract_version,
                ),
                context,
                finance_research_id=finance_research_id,
                created_at=created_at,
            )
            accepted = FinanceResearchAcceptedResult.from_domain(result)
            await uow.researches.add(
                FinanceResearchRecord(
                    finance_research_id=accepted.finance_research_id,
                    tenant_id=context.tenant_id,
                    actor_id=context.actor_id,
                    request_id=accepted.request_id,
                    source_domain=accepted.source_domain,
                    source_reference=accepted.source_reference,
                    instrument=accepted.instrument,
                    recommendation=accepted.recommendation,
                    confidence=accepted.confidence,
                    issues=accepted.issues,
                    correlation_id=accepted.correlation_id,
                    created_at=accepted.created_at,
                    replayed=accepted.replayed,
                    status=accepted.status,
                    contract_version=accepted.contract_version,
                )
            )
            await uow.audit.add(
                AuditEntry(
                    entry_id=self._id_generator.new_uuid(),
                    context=context,
                    action="finance.research.created",
                    target_type="finance_research",
                    target_id=accepted.finance_research_id,
                    result="success",
                    risk="medium",
                    occurred_at=created_at,
                    metadata={
                        "contract_version": "1",
                        "request_id": str(accepted.request_id),
                        "source_domain": accepted.source_domain,
                    },
                )
            )
            await uow.idempotency.add(
                StoredCommandResult(
                    scope=scope,
                    fingerprint=fingerprint,
                    response_status=201,
                    result=accepted.stored(),
                    target_id=accepted.finance_research_id,
                    correlation_id=context.correlation_id,
                    created_at=created_at,
                    expires_at=created_at + _REPLAY_WINDOW,
                )
            )
            return accepted


def _command_scope(context: RequestContext, raw_key: str) -> CommandScope:
    normalized = raw_key.strip()
    if not normalized or len(normalized) > 200:
        raise InvalidIdempotencyKeyError(
            "Idempotency-Key must contain between 1 and 200 characters."
        )
    return CommandScope(
        tenant_id=context.tenant_id,
        actor_id=context.actor_id,
        operation=_OPERATION,
        key_hash=hashlib.sha256(normalized.encode()).hexdigest(),
    )


def _fingerprint(command: CreateFinanceResearch) -> str:
    payload = {
        "operation": _OPERATION,
        "version": 1,
        "request_id": str(command.request_id),
        "source_domain": command.source_domain,
        "source_reference": command.source_reference,
        "instrument": command.instrument,
        "objective": command.objective,
        "thesis": command.thesis,
        "horizon_days": command.horizon_days,
        "domain_context": command.domain_context,
        "research": [
            {"summary": item.summary, "facts": item.facts} for item in command.research
        ],
        "sources": [
            {
                "source_reference": item.source_reference,
                "title": item.title,
                "url": item.url,
                "as_of": item.as_of.isoformat() if item.as_of else None,
            }
            for item in command.sources
        ],
        "constraints": command.constraints,
        "quality_metadata": command.quality_metadata,
    }
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode()).hexdigest()


def _replay_result(
    stored: StoredCommandResult, correlation_id: str
) -> FinanceResearchAcceptedResult:
    result = stored.result
    return FinanceResearchAcceptedResult(
        finance_research_id=UUID(result["finance_research_id"]),
        request_id=UUID(result["request_id"]),
        source_domain=result["source_domain"],
        source_reference=result["source_reference"],
        instrument=result["instrument"],
        recommendation=result["recommendation"],
        confidence=float(result["confidence"]),
        issues=tuple(json.loads(result.get("issues", "[]"))),
        correlation_id=correlation_id,
        created_at=datetime.fromisoformat(result["created_at"]),
        replayed=result.get("replayed", "true") == "true",
        status=result["status"],
        contract_version=int(result["contract_version"]),
    )
