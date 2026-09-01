FROM ghcr.io/astral-sh/uv:0.12.0-python3.13-trixie-slim

WORKDIR /workspace
COPY pyproject.toml uv.lock ./
COPY applications ./applications
COPY services ./services
RUN uv sync --locked --no-dev --package finance-worker

CMD ["/workspace/.venv/bin/finance-worker"]
