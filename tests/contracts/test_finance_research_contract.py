import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load_json(path: Path) -> dict[str, object]:
    value: dict[str, object] = json.loads(path.read_text(encoding="utf-8"))
    return value


def validate_create_finance_research_request(instance: dict[str, object]) -> None:
    required = {
        "contract_version",
        "request_id",
        "source_domain",
        "source_reference",
        "instrument",
        "objective",
        "domain_context",
    }
    missing = sorted(required.difference(instance))
    assert not missing, f"missing required fields: {', '.join(missing)}"
    assert instance["contract_version"] == 1
    assert instance["source_domain"] == "finance"
    assert isinstance(instance["domain_context"], dict)
    assert instance["domain_context"]["review_status"] == "finance-reviewed"
    assert isinstance(instance["research"], list)
    assert isinstance(instance["sources"], list)
    assert isinstance(instance["constraints"], list)
    assert instance["instrument"] == "AAPL"


def validate_finance_research_accepted_response(
    instance: dict[str, object],
) -> None:
    required = {
        "contract_version",
        "finance_research_id",
        "request_id",
        "source_domain",
        "source_reference",
        "instrument",
        "recommendation",
        "confidence",
        "issues",
        "correlation_id",
        "created_at",
        "replayed",
        "status",
    }
    missing = sorted(required.difference(instance))
    assert not missing, f"missing required fields: {', '.join(missing)}"
    assert instance["status"] == "accepted"
    assert instance["source_domain"] == "finance"
    assert isinstance(instance["issues"], list)
    assert isinstance(instance["confidence"], (int, float))


def test_finance_request_matches_v1_provider_contract() -> None:
    request = load_json(
        ROOT / "contracts" / "fixtures" / "create-finance-research.v1.json"
    )

    validate_create_finance_research_request(request)


def test_finance_accepted_response_matches_provider_contract() -> None:
    response = load_json(
        ROOT / "contracts" / "fixtures" / "finance-research-accepted.v1.json"
    )

    validate_finance_research_accepted_response(response)
    assert response["request_id"] == "30000000-0000-0000-0000-000000000010"


def test_provider_contract_rejects_request_without_instrument() -> None:
    request = load_json(
        ROOT / "contracts" / "fixtures" / "create-finance-research.v1.json"
    )
    del request["instrument"]

    try:
        validate_create_finance_research_request(request)
    except AssertionError as error:
        assert "instrument" in str(error)
    else:
        raise AssertionError("provider schema accepted a request without instrument")


def test_acceptance_record_pins_contract_and_consumer_evidence() -> None:
    acceptance = load_json(ROOT / "contracts" / "acceptance" / "finance-research-v1.json")

    assert acceptance["technical_status"] == "accepted"
    assert acceptance["governance_status"] == "pending_accountable_owner"
    snapshot = ROOT / acceptance["provider_contract_snapshot"]
    snapshot_hash = hashlib.sha256(snapshot.read_bytes()).hexdigest()

    assert acceptance["provider_contract_sha256"] == snapshot_hash
    assert (ROOT / acceptance["consumer_test_reference"]).is_file()
