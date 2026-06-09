#!/usr/bin/env bash
# VALEN v1.0.0 — atualizacao do projeto
set -euo pipefail

echo "==> VALEN update"

echo "==> git pull"
git pull --ff-only

echo "==> atualizando dependencias"
uv sync --extra dev

if command -v docker >/dev/null 2>&1; then
    echo "==> rebuild e restart dos containers"
    docker compose pull
    docker compose up -d --build
fi

echo "==> update concluido"
