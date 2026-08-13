from finance_api import create_app


def test_finance_api_app_builds() -> None:
    app = create_app()

    assert app.title == "AI Platform Finance API"

