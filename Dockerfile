# VALEN v1.0.0 — API container
FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# uv: gerenciador de dependencias oficial do projeto
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# curl necessario para o healthcheck do compose
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Projeto + codigo (hatchling precisa de valen/ para construir o wheel)
COPY pyproject.toml ./
COPY valen ./valen
RUN uv pip install --system --no-cache .

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "valen.main:app", "--host", "0.0.0.0", "--port", "8000"]
