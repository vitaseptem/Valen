-- migrations/001_initial.sql

-- Event Store (imutável — NUNCA UPDATE ou DELETE)
CREATE TABLE IF NOT EXISTS domain_events (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type      VARCHAR(100) NOT NULL,
    aggregate_id    VARCHAR(100) NOT NULL,
    aggregate_type  VARCHAR(50) NOT NULL,
    payload         JSONB NOT NULL,
    metadata        JSONB NOT NULL DEFAULT '{}',
    version         INTEGER NOT NULL,
    occurred_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (aggregate_id, version)
);
CREATE INDEX IF NOT EXISTS idx_events_aggregate ON domain_events (aggregate_id, version);
CREATE INDEX IF NOT EXISTS idx_events_type_time ON domain_events (event_type, occurred_at);

-- Audit Trail (append-only — NUNCA UPDATE ou DELETE)
CREATE TABLE IF NOT EXISTS audit_trail (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id        VARCHAR(50) NOT NULL,
    tool_name       VARCHAR(100) NOT NULL,
    action          VARCHAR(100) NOT NULL,
    args_hash       VARCHAR(64) NOT NULL,
    tier            VARCHAR(20) NOT NULL,
    sandbox_mode    VARCHAR(20) NOT NULL,
    dry_run         BOOLEAN NOT NULL DEFAULT FALSE,
    result_ok       BOOLEAN NOT NULL,
    duration_ms     INTEGER NOT NULL,
    audit_hash      VARCHAR(64) NOT NULL,
    session_id      VARCHAR(100),
    executed_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_audit_agent ON audit_trail (agent_id, executed_at);
CREATE INDEX IF NOT EXISTS idx_audit_tool ON audit_trail (tool_name, executed_at);

-- NeuroValen: notas
CREATE TABLE IF NOT EXISTS neurovalen_notes (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title       VARCHAR(500) NOT NULL,
    content     TEXT NOT NULL,
    note_type   VARCHAR(50) NOT NULL,
    tags        TEXT[] NOT NULL DEFAULT '{}',
    priority    VARCHAR(10) NOT NULL DEFAULT 'medium',
    created_by  VARCHAR(50),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_notes_tags ON neurovalen_notes USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_notes_type ON neurovalen_notes (note_type);

-- Sessões ativas
CREATE TABLE IF NOT EXISTS agent_sessions (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id    VARCHAR(50) NOT NULL,
    user_id     VARCHAR(100) NOT NULL,
    status      VARCHAR(20) NOT NULL DEFAULT 'idle',
    started_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at    TIMESTAMPTZ,
    metadata    JSONB NOT NULL DEFAULT '{}'
);

-- Plugins instalados (para Marketplace futuro)
CREATE TABLE IF NOT EXISTS installed_plugins (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plugin_id       VARCHAR(100) UNIQUE NOT NULL,
    name            VARCHAR(200) NOT NULL,
    version         VARCHAR(20) NOT NULL,
    plugin_type     VARCHAR(20) NOT NULL,
    config          JSONB NOT NULL DEFAULT '{}',
    enabled         BOOLEAN NOT NULL DEFAULT TRUE,
    installed_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
