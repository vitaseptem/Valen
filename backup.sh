#!/usr/bin/env bash
# VALEN v1.0.0 — backup de PostgreSQL e MinIO
# NOTA: na operacao normal, backups sao gerenciados pelo agente Nexus.
# Este script e o fallback manual.
set -euo pipefail

STAMP="$(date +%Y%m%d_%H%M%S)"
DEST="${VALEN_BACKUP_DIR:-./backups}/$STAMP"
mkdir -p "$DEST"

echo "==> backup VALEN -> $DEST"

# PostgreSQL
if docker ps --format '{{.Names}}' | grep -q '^valen-postgres$'; then
    echo "==> dump postgres"
    docker exec valen-postgres pg_dump -U valen valen | gzip > "$DEST/postgres.sql.gz"
fi

# MinIO (object storage) via mirror, se o client mc estiver disponivel
if command -v mc >/dev/null 2>&1; then
    echo "==> mirror minio"
    mc mirror --quiet valen/ "$DEST/minio/" || echo "!! mc nao configurado, pulei minio"
fi

echo "==> backup concluido: $DEST"
