FROM ghcr.io/astral-sh/uv:0.12.0-python3.13-trixie-slim

WORKDIR /workspace
COPY pyproject.toml uv.lock ./
COPY applications ./applications
COPY services ./services
RUN uv sync --locked --no-dev --package finance-api-fastapi

EXPOSE 8011
HEALTHCHECK --interval=5s --timeout=5s --retries=20 CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8011/livez')"]
CMD ["/workspace/.venv/bin/finance-api"]
