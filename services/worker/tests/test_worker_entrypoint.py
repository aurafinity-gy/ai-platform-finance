import finance_worker
import pytest


def test_finance_worker_package_imports() -> None:
    assert finance_worker.run is not None


def test_worker_runtime_settings_require_database_identity() -> None:
    with pytest.raises(ValueError, match="FINANCE_DATABASE_URL"):
        finance_worker.WorkerRuntimeSettings.from_environment({})


def test_worker_runtime_settings_parse_database_identity() -> None:
    settings = finance_worker.WorkerRuntimeSettings.from_environment(
        {
            "FINANCE_DATABASE_URL": "postgresql://worker:test@localhost/postgres",
            "FINANCE_WORKER_ACTOR_ID": "30000000-0000-0000-0000-000000000001",
            "FINANCE_WORKER_TENANT_ID": "30000000-0000-0000-0000-000000000002",
        }
    )

    assert str(settings.actor_id) == "30000000-0000-0000-0000-000000000001"
    assert str(settings.tenant_id) == "30000000-0000-0000-0000-000000000002"
