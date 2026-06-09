#!/usr/bin/env bash
# VALEN v1.0.0 — setup inicial do ambiente
set -euo pipefail

echo "==> VALEN setup"

# 1. uv (gerenciador de dependencias)
if ! command -v uv >/dev/null 2>&1; then
    echo "==> instalando uv"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
fi

# 2. .env
if [ ! -f .env ]; then
    echo "==> criando .env a partir de .env.example (preencha os segredos)"
    cp .env.example .env
fi

# 3. dependencias Python (uv gerencia o proprio Python 3.11+)
echo "==> instalando dependencias com uv"
uv sync --extra dev

# 4. infraestrutura via Docker
if command -v docker >/dev/null 2>&1; then
    echo "==> subindo infraestrutura (postgres, redis, qdrant, minio)"
    docker compose up -d postgres redis qdrant minio
else
    echo "!! docker nao encontrado — pulei a subida da infraestrutura"
fi

echo "==> setup concluido"
