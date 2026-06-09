# VALEN v1.0.0 — MASTER PROMPT FASE 0
# Para uso no Claude Code (terminal)
# Criado por: Astraz Studio · Junho 2026

---

## CONTEXTO OBRIGATÓRIO — LEIA ANTES DE QUALQUER AÇÃO

Você está iniciando o projeto **VALEN v1.0.0** do zero.
O repositório existe em `https://github.com/vitaseptem/Valen.git` mas **todo o código antigo deve ser ignorado**.
Estamos construindo uma base nova, limpa e sólida.

**Não existe código a preservar. Não existe nada a migrar. Começamos do zero.**

---

## IDENTIDADE DO PROJETO

- **Nome oficial:** VALEN
- **Versão:** 1.0.0
- **Criado por:** Astraz Studio
- **Cérebro central:** NeuroValen
- **Data:** Junho 2026

---

## AMBIENTE DE EXECUÇÃO

- **Servidor:** Oracle Cloud Free Tier (VPS)
- **Sistema:** Ubuntu 22.04 LTS x86_64
- **Acesso remoto:** SSH via Termux (Android) — Termux é APENAS cliente SSH
- **Runtime:** Docker + Docker Compose (obrigatório para todos os serviços)
- **Sessão:** tmux para processos persistentes

---

## STACK TÉCNICA DEFINITIVA

### Backend
- **Python 3.11+**
- **FastAPI** (REST + WebSocket)
- **Pydantic v2** para todos os modelos
- **asyncpg** para PostgreSQL
- **aioredis** para Redis
- **qdrant-client** para Qdrant
- **minio** para MinIO
- **uv** como gerenciador de dependências (não pip direto)

### Bancos de Dados (todos via Docker)
- **PostgreSQL 16** — banco relacional principal (Event Store, Audit Trail, configs)
- **Redis 7** — cache, sessões, pub/sub entre agentes, filas
- **Qdrant** — banco vetorial para o NeuroValen (busca semântica)
- **MinIO** — object storage (screenshots, imagens, backups, builds)

### Providers de IA (Fase 0: apenas estrutura, sem chamadas reais)
- **Groq** — prioridade para uso diário (alta velocidade)
- **Ollama** — local, sem custo, privacidade máxima
- Outros (Anthropic, OpenAI, Gemini, Grok) — suportados via arquitetura modular

### Observabilidade (configurar estrutura, sem precisar rodar tudo agora)
- Prometheus + Grafana + OpenTelemetry + Sentry

---

## OS 4 AGENTES — REGRA ABSOLUTA

Apenas **4 agentes** existem no sistema. Nenhum a mais.

| Agente | Símbolo | Papel |
|--------|---------|-------|
| CEO | ♛ | Interface principal com o usuário. Orquestrador. Personalidade: Jarvis + Tony Stark. Trata o usuário sempre de "meu rei". |
| Forge | ⚒ | Criação de código, projetos, scripts. Cauteloso por padrão, direto quando autorizado. |
| Nexus | ⬢ | Infraestrutura, Docker, monitoramento, saúde do sistema, backups. |
| Analyst | ◇ | Análise profunda, relatórios, raciocínio estratégico. |

**Regra inquebrável R2:** qualquer agente além desses 4 vira Tool ou Service. Nunca agente.

---

## SISTEMA DE TOOLS + SANDBOX — PILAR CENTRAL

Este é o sistema mais importante da v1.0.0. Nada acontece fora dele.

### Estrutura base (Python):

```python
from typing import Any, Literal
from dataclasses import dataclass, field
from datetime import datetime
import hashlib, json

@dataclass
class ToolResult:
    ok: bool
    result: Any = None
    error: str | None = None
    duration_ms: int = 0
    audit_hash: str = ""
    metadata: dict = field(default_factory=dict)

@dataclass
class ToolContext:
    agent_id: str
    user_id: str
    session_id: str
    permissions: set[str]
    sandbox_mode: Literal["safe", "restricted", "docker", "unrestricted"]
    dry_run: bool = False

class ToolBase:
    name: str
    description: str
    version: str = "1.0.0"
    required_permissions: set[str]
    risk_level: Literal["low", "medium", "high", "critical"]
    timeout_seconds: int = 60
    sandbox_mode: Literal["safe", "restricted", "docker"] = "safe"

    async def validate(self, action: str, args: dict, context: ToolContext) -> bool: ...
    async def run(self, action: str, args: dict, context: ToolContext) -> ToolResult: ...
    async def audit(self, action: str, args: dict, result: ToolResult, context: ToolContext) -> None: ...
```

### Execution Tiers (classificação de risco obrigatória):

| Tier | Exemplos | Pede Aprovação? |
|------|----------|----------------|
| `READ_ONLY` | ls, cat, ps, df, curl GET | Não |
| `REVERSIBLE` | mkdir, cp, echo, curl POST | Não (dry-run padrão) |
| `DESTRUCTIVE` | rm, mv, sed -i, truncate | Sim, sempre |
| `SYSTEM_LEVEL` | systemctl, docker, apt, kill | Sim, sempre |

### Sandbox Modes:

| Modo | Quem usa | Restrição |
|------|----------|-----------|
| `safe` | Forge, Analyst | Máxima |
| `restricted` | CEO | Alta |
| `docker` | Nexus | Máxima + isolamento de rede |
| `unrestricted` | CEO com aprovação documentada | Nenhuma |

### ALWAYS_BLOCKED (nunca executar, independente de permissão):
```python
ALWAYS_BLOCKED = [
    r"rm\s+-rf\s+/", r"rm\s+-rf\s+\*", r"rm\s+-rf\s+~",
    "dd if=", "mkfs", "format", "fdisk", "parted",
    "reboot", "shutdown", "halt", "poweroff", "init 0", "init 6",
    "sudo ", "su -", "doas ",
    "chmod 777", "chown -R root",
    "pkill -f valen", "killall python", "kill -9 1",
]
```

### ACL por agente:
```python
AGENT_PERMISSIONS = {
    "CEO":     {"read", "write", "execute", "network", "memory", "docker_inspect"},
    "Forge":   {"read", "write", "execute", "memory"},
    "Nexus":   {"read", "write", "execute", "network", "docker_full", "memory", "system_monitor"},
    "Analyst": {"read", "memory", "network_read"},
}
```

### Tools obrigatórias na v1.0.0:

| Tool | Responsabilidade | Tier máx | Agente principal |
|------|-----------------|----------|-----------------|
| FilesystemTool | Leitura e escrita de arquivos | DESTRUCTIVE | Forge |
| TerminalTool | Execução de comandos shell com Sandbox | SYSTEM_LEVEL | Forge, Nexus |
| MemoryTool | Leitura e escrita no NeuroValen | REVERSIBLE | Todos |
| NetworkTool | HTTP e monitoramento de rede | REVERSIBLE | Nexus, CEO |
| DockerTool | Gerenciamento de containers | SYSTEM_LEVEL | Nexus |
| ProviderTool | Interface com LLMs externos | REVERSIBLE | Todos |
| BrowserTool | Navegação e scraping | REVERSIBLE | CEO, Forge |
| VisionTool | Análise de imagens | READ_ONLY | CEO, Analyst |
| EventTool | Lembretes e agendamentos | REVERSIBLE | CEO |

### Audit Trail (imutável — toda execução gera uma entrada):
```json
{
  "timestamp": "ISO8601",
  "agent_id": "Forge",
  "tool_name": "FilesystemTool",
  "action": "write_file",
  "args_hash": "sha256:...",
  "tier": "REVERSIBLE",
  "sandbox_mode": "safe",
  "dry_run": false,
  "result_ok": true,
  "duration_ms": 45,
  "audit_hash": "sha256:..."
}
```

---

## NEUROVALEN — CÉREBRO CENTRAL

- Nome oficial: **NeuroValen**
- Único repositório de memória de longo prazo
- Nenhum agente acessa diretamente — sempre via `MemoryTool`
- Notas em Markdown + frontmatter semântico
- Busca híbrida: semântica (Qdrant) + full-text (PostgreSQL FTS)
- Backups automáticos gerenciados pelo Nexus

### Formato das notas:
```markdown
---
type: architecture | concept | decision | log | agent | visual
tags: [tag1, tag2]
created: 2026-06-09
priority: low | medium | high
---

Conteúdo da nota aqui...

Referência para [[outra-nota]]
```

---

## PROVIDERS DE IA — ARQUITETURA MODULAR

```python
from abc import ABC, abstractmethod
from typing import AsyncGenerator

class ProviderBase(ABC):
    name: str
    model: str
    api_key_env: str
    supports_streaming: bool
    supports_vision: bool
    supports_tools: bool
    max_context_tokens: int

    @abstractmethod
    async def complete(self, messages: list, tools: list | None = None) -> "ProviderResponse": ...

    @abstractmethod
    async def stream(self, messages: list) -> AsyncGenerator[str, None]: ...
```

### Providers a implementar (nesta ordem):
1. **GroqProvider** — `llama3-70b-8192`, `mixtral-8x7b-32768`
2. **OllamaProvider** — local, endpoint configurável
3. Os demais (Anthropic, OpenAI, Gemini, Grok) — stubs preparados para ativar depois

### Fallback automático:
- Provider padrão configurável via `.env`
- Se falhar → tenta próximo na lista de prioridade
- Nexus monitora latência e saúde de todos em tempo real

---

## ESTRUTURA DE PASTAS OBRIGATÓRIA

```
valen/
├── pyproject.toml                  # versão 1.0.0
├── Dockerfile
├── docker-compose.yml
├── docker-compose.observability.yml
├── .env.example
├── README.md
├── PROJECT.md
├── CHANGELOG.md
├── setup.sh
├── update.sh
├── backup.sh
│
├── valen/
│   ├── __init__.py                 # version = "1.0.0"
│   ├── main.py                     # FastAPI app + WebSocket
│   ├── config.py                   # settings via Pydantic BaseSettings
│   │
│   ├── domains/
│   │   ├── agents/
│   │   │   ├── entities/           # Agent, AgentState, AgentMessage
│   │   │   ├── value_objects/      # AgentId, Permission, SandboxMode
│   │   │   ├── repositories/       # IAgentRepository (Protocol)
│   │   │   ├── services/           # AgentOrchestrationService
│   │   │   ├── events/             # AgentStarted, AgentFailed, AgentCompleted
│   │   │   └── commands/           # RunAgentCommand, StopAgentCommand
│   │   │
│   │   ├── memory/
│   │   │   ├── entities/           # Note, NoteLink, Memory
│   │   │   ├── repositories/       # IMemoryRepository (Protocol)
│   │   │   └── services/           # MemorySearchService
│   │   │
│   │   ├── tools/
│   │   │   ├── base.py             # ToolBase, ToolResult, ToolContext
│   │   │   ├── sandbox.py          # Sandbox, ExecutionTiers, ALWAYS_BLOCKED
│   │   │   ├── acl.py              # ACL, AGENT_PERMISSIONS
│   │   │   ├── audit.py            # AuditTrail
│   │   │   └── implementations/
│   │   │       ├── filesystem.py   # FilesystemTool
│   │   │       ├── terminal.py     # TerminalTool
│   │   │       ├── memory.py       # MemoryTool
│   │   │       ├── network.py      # NetworkTool
│   │   │       ├── docker_tool.py  # DockerTool
│   │   │       └── provider.py     # ProviderTool
│   │   │
│   │   ├── providers/
│   │   │   ├── base.py             # ProviderBase (ABC)
│   │   │   ├── groq.py             # GroqProvider
│   │   │   ├── ollama.py           # OllamaProvider
│   │   │   ├── anthropic.py        # AnthropicProvider (stub)
│   │   │   ├── openai.py           # OpenAIProvider (stub)
│   │   │   └── registry.py         # ProviderRegistry + fallback
│   │   │
│   │   └── observability/
│   │       ├── metrics.py          # Prometheus counters/histograms/gauges
│   │       ├── tracing.py          # OpenTelemetry setup
│   │       └── logging.py          # Structured JSON logging
│   │
│   ├── infrastructure/
│   │   ├── database/
│   │   │   ├── postgres.py         # asyncpg pool + migrations
│   │   │   ├── redis.py            # aioredis connection
│   │   │   ├── qdrant.py           # qdrant-client setup + collections
│   │   │   └── minio.py            # MinIO client + buckets
│   │   └── migrations/
│   │       └── 001_initial.sql     # Event Store + Audit Trail schema
│   │
│   ├── application/
│   │   ├── commands/               # Command handlers (CQRS)
│   │   └── queries/                # Query handlers (CQRS)
│   │
│   └── interfaces/
│       ├── api/
│       │   ├── routes/             # FastAPI routers
│       │   └── websocket/          # WebSocket handlers
│       └── cli/                    # CLI commands (status, health, etc.)
│
└── tests/
    ├── unit/
    │   └── tools/                  # Testes unitários do sistema de Tools
    └── integration/
        └── tools/                  # Testes de integração com DB real
```

---

## DOCKER COMPOSE — CONFIGURAÇÃO COMPLETA

```yaml
# docker-compose.yml
version: "3.9"

services:
  valen:
    build: .
    container_name: valen-api
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - POSTGRES_URL=${POSTGRES_URL}
      - REDIS_URL=${REDIS_URL}
      - QDRANT_URL=${QDRANT_URL}
      - MINIO_ENDPOINT=${MINIO_ENDPOINT}
      - GROQ_API_KEY=${GROQ_API_KEY}
      - OLLAMA_URL=${OLLAMA_URL}
    volumes:
      - ./valen:/app/valen
      - valen-data:/app/data
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      qdrant:
        condition: service_healthy
      minio:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    labels:
      - "valen.version=1.0.0"

  postgres:
    image: postgres:16-alpine
    container_name: valen-postgres
    restart: unless-stopped
    environment:
      POSTGRES_DB: valen
      POSTGRES_USER: valen
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./valen/infrastructure/migrations:/docker-entrypoint-initdb.d
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U valen"]
      interval: 10s
      timeout: 5s
      retries: 5
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    container_name: valen-redis
    restart: unless-stopped
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis-data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    ports:
      - "6379:6379"

  qdrant:
    image: qdrant/qdrant:latest
    container_name: valen-qdrant
    restart: unless-stopped
    volumes:
      - qdrant-data:/qdrant/storage
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:6333/health"]
      interval: 15s
      timeout: 5s
      retries: 5
    ports:
      - "6333:6333"

  minio:
    image: minio/minio:latest
    container_name: valen-minio
    restart: unless-stopped
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_ACCESS_KEY}
      MINIO_ROOT_PASSWORD: ${MINIO_SECRET_KEY}
    volumes:
      - minio-data:/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 15s
      timeout: 5s
      retries: 5
    ports:
      - "9000:9000"
      - "9001:9001"

volumes:
  valen-data:
  postgres-data:
  redis-data:
  qdrant-data:
  minio-data:
```

---

## SCHEMA INICIAL DO POSTGRESQL

```sql
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
```

---

## ARQUIVO .env.example

```env
# VALEN v1.0.0 — Environment Variables

# PostgreSQL
POSTGRES_URL=postgresql://valen:password@localhost:5432/valen
POSTGRES_PASSWORD=change_me_in_production

# Redis
REDIS_URL=redis://:password@localhost:6379/0
REDIS_PASSWORD=change_me_in_production

# Qdrant
QDRANT_URL=http://localhost:6333

# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=valen_admin
MINIO_SECRET_KEY=change_me_in_production
MINIO_SECURE=false

# Providers de IA
GROQ_API_KEY=gsk_...
OLLAMA_URL=http://localhost:11434
ANTHROPIC_API_KEY=sk-ant-...  # opcional na v1.0.0
OPENAI_API_KEY=sk-...          # opcional
GEMINI_API_KEY=...             # opcional
GROK_API_KEY=...               # opcional

# VALEN Config
VALEN_ENV=development
VALEN_VERSION=1.0.0
VALEN_DEFAULT_PROVIDER=groq
VALEN_FALLBACK_PROVIDERS=ollama,anthropic
VALEN_LOG_LEVEL=INFO
VALEN_AUTONOMY_LEVEL=5

# Sentry (opcional na v1.0.0)
SENTRY_DSN=

# Segurança
VALEN_SECRET_KEY=change_me_32_chars_minimum
```

---

## pyproject.toml BASE

```toml
[project]
name = "valen"
version = "1.0.0"
description = "VALEN — Plataforma autônoma de desenvolvimento e vida pessoal"
authors = [{ name = "Astraz Studio" }]
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.111.0",
    "uvicorn[standard]>=0.29.0",
    "websockets>=12.0",
    "pydantic>=2.7.0",
    "pydantic-settings>=2.2.0",
    "asyncpg>=0.29.0",
    "redis[asyncio]>=5.0.0",
    "qdrant-client>=1.9.0",
    "minio>=7.2.0",
    "httpx>=0.27.0",
    "groq>=0.9.0",
    "ollama>=0.2.0",
    "opentelemetry-api>=1.24.0",
    "opentelemetry-sdk>=1.24.0",
    "prometheus-client>=0.20.0",
    "structlog>=24.1.0",
    "python-dotenv>=1.0.0",
    "typer>=0.12.0",
    "rich>=13.7.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=5.0.0",
    "httpx>=0.27.0",
    "ruff>=0.4.0",
    "mypy>=1.10.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.mypy]
python_version = "3.11"
strict = true

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

---

## QUALIDADE TÉCNICA EXIGIDA (não negociável)

- ✅ **Type hints completos** em todo lugar (Python 3.11+)
- ✅ **Pydantic v2** para todos os modelos de dados
- ✅ **async/await** em toda a stack de I/O
- ✅ **Logging estruturado JSON** com structlog (níveis: DEBUG, INFO, WARNING, ERROR)
- ✅ **Timeouts** em todas as operações externas
- ✅ **Retry com backoff exponencial** para providers e rede
- ✅ **Docstrings** em todas as classes e funções públicas
- ✅ **Testes** para todo o sistema de Tools antes de avançar para Fase 1

---

## REGRAS INQUEBRÂVEIS

- ❌ Nunca criar agentes além dos 4 (CEO, Forge, Nexus, Analyst)
- ❌ Nunca executar comandos shell direto no código dos agentes — sempre via ToolBase
- ❌ Nunca deletar arquivos sem confirmação explícita
- ❌ Nunca complexidade desnecessária — simples e funcional > elegante e quebrado
- ❌ Nunca pular testes do sistema de Tools
- ❌ Nunca fazer tudo de uma vez — seguir as fases em ordem

---

## INSTRUÇÃO PARA O CLAUDE CODE — FASE 0

**Sua tarefa agora, e apenas ela:**

1. Clone (ou inicialize) o repositório `https://github.com/vitaseptem/Valen.git`
2. **Apague todo o código antigo** (preserve apenas o `.git`)
3. Crie toda a estrutura de pastas descrita acima
4. Crie os arquivos base: `pyproject.toml`, `Dockerfile`, `docker-compose.yml`, `.env.example`, `README.md`, `PROJECT.md`, `CHANGELOG.md`
5. Crie o schema SQL inicial em `valen/infrastructure/migrations/001_initial.sql`
6. Crie os stubs (arquivos vazios com estrutura básica) de todos os módulos
7. Configure `uv` e instale as dependências
8. Crie o arquivo `VALEN_v1.0.0_REFACTOR_PLAN.md` na raiz do projeto documentando:
   - O que foi apagado e por quê
   - A estrutura nova que foi criada
   - O plano exato de implementação fase a fase
   - Dependências e riscos identificados
9. **Pare aqui** e apresente o resultado ao usuário antes de continuar

**Após a Fase 0 estar concluída e validada, a Fase 1 começa:**
- Implementar `ToolBase`, `ToolResult`, `ToolContext`
- Implementar `Sandbox` com todos os Execution Tiers
- Implementar `ACL` com `AGENT_PERMISSIONS`
- Implementar `AuditTrail` imutável com hash
- Implementar `FilesystemTool`, `TerminalTool`, `MemoryTool`
- Escrever testes cobrindo todos os tiers e modos
- Só avançar para Fase 2 após testes passando

---

## FASES RESUMIDAS

| Fase | O que fazer | Confirmação necessária |
|------|------------|----------------------|
| **0** | Estrutura do projeto + plano de refatoração | ✅ Antes de continuar |
| **1** | Sistema de Tools + Sandbox + ACL + Audit Trail | ✅ Antes de continuar |
| **2** | NeuroValen (notas, busca híbrida, MemoryTool) | ✅ Antes de continuar |
| **3** | Os 4 Agentes usando exclusivamente Tools | ✅ Antes de continuar |
| **4** | Providers (Groq + Ollama) + comunicação inter-agentes | ✅ Antes de continuar |
| **5** | FastAPI + WebSocket + interface visual (núcleo neural) | ✅ Antes de continuar |
| **6** | Testes, documentação, versão 1.0.0 em tudo | ✅ Entrega final |

---

*VALEN v1.0.0 — Master Prompt Fase 0*
*Astraz Studio · Junho 2026*
*Gerado com base nos arquivos: VALEN_v1_0_0_MASTER_PROMPT_v4_ULTRA_DETALHADO.md + README_Index.md + VALEN_Vault_Engine_v1_Master_Prompt.md + valen-cli-master-prompt.md*
