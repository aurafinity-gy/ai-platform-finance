import uvicorn

from finance_api_service.app import create_runtime_app


def run() -> None:
    uvicorn.run(create_runtime_app(), host="0.0.0.0", port=8011)


if __name__ == "__main__":
    run()

