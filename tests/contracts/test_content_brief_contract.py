import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load_json(path: Path) -> dict[str, object]:
    value: dict[str, object] = json.loads(path.read_text(encoding="utf-8"))
    return value


def validate_create_content_brief_request(instance: dict[str, object]) -> None:
    required = {
        "contract_version",
        "request_id",
        "source_domain",
        "source_reference",
        "topic",
        "objective",
        "audience",
        "domain_context",
    }
    missing = sorted(required.difference(instance))
    assert not missing, f"missing required fields: {', '.join(missing)}"
    assert instance["contract_version"] == 1
    assert instance["source_domain"] == "finance"
    assert isinstance(instance["domain_context"], dict)
    assert instance["domain_context"]["as_of"] == "2026-08-12T15:00:00Z"
    quality_metadata = instance["quality_metadata"]
    assert isinstance(quality_metadata, dict)
    assert quality_metadata["review_status"] == "finance-reviewed"
    assert isinstance(instance["research"], list)
    assert isinstance(instance["sources"], list)


def validate_content_accepted_response(instance: dict[str, object]) -> None:
    required = {
        "contract_version",
        "content_brief_id",
        "request_id",
        "source_domain",
        "source_reference",
        "status",
        "requested_channels",
        "issues",
        "correlation_id",
        "created_at",
        "replayed",
    }
    missing = sorted(required.difference(instance))
    assert not missing, f"missing required fields: {', '.join(missing)}"
    assert instance["status"] == "accepted"
    assert isinstance(instance["requested_channels"], list)
    assert isinstance(instance["issues"], list)


def test_finance_request_matches_content_v1_provider_contract() -> None:
    request = load_json(
        ROOT / "contracts" / "fixtures" / "create-content-brief.v1.json"
    )

    validate_create_content_brief_request(request)


def test_content_accepted_response_matches_provider_contract() -> None:
    response = load_json(
        ROOT / "contracts" / "fixtures" / "content-brief-accepted.v1.json"
    )

    validate_content_accepted_response(response)
    assert response["request_id"] == "30000000-0000-0000-0000-000000000001"


def test_provider_contract_rejects_request_without_finance_source_reference() -> None:
    request = load_json(
        ROOT / "contracts" / "fixtures" / "create-content-brief.v1.json"
    )
    del request["source_reference"]

    try:
        validate_create_content_brief_request(request)
    except AssertionError as error:
        assert "source_reference" in str(error)
    else:
        raise AssertionError("provider schema accepted a request without source_reference")


def test_acceptance_record_pins_contract_and_consumer_evidence() -> None:
    acceptance = load_json(ROOT / "contracts" / "acceptance" / "content-brief-v1.json")

    assert acceptance["technical_status"] == "accepted"
    assert acceptance["governance_status"] == "pending_accountable_owner"
    snapshot = ROOT / acceptance["provider_contract_snapshot"]
    snapshot_hash = hashlib.sha256(snapshot.read_bytes()).hexdigest()

    assert acceptance["provider_contract_sha256"] == snapshot_hash
    assert (ROOT / acceptance["consumer_test_reference"]).is_file()
