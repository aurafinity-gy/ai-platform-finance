import finance_worker


def test_finance_worker_package_imports() -> None:
    assert finance_worker.run is not None

