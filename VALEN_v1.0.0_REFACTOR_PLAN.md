# VALEN v1.0.0 — REFACTOR PLAN

Documento gerado na **Fase 0**. Registra o que foi feito, a estrutura nova e o
plano exato de implementação fase a fase.

*Astraz Studio · 2026-06-09*

---

## 1. O que foi apagado e por quê

**Nada de código foi apagado.**

O repositório `https://github.com/vitaseptem/Valen.git` foi clonado num diretório
que continha apenas o `.git` e o arquivo `VALEN_v1.0.0_FASE0_MASTER_PROMPT.md`
(a especificação). Não havia código-fonte antigo a preservar ou migrar.

Decisão: **manter** `VALEN_v1.0.0_FASE0_MASTER_PROMPT.md` na raiz — é a fonte da
especificação, não código legado. Toda a base nova foi construída do zero a partir
dele.

---

## 2. Estrutura nova criada

### Arquivos de raiz

| Arquivo | Função |
|---------|--------|
| `pyproject.toml` | Projeto v1.0.0, deps, ruff/mypy/pytest, build hatchling |
| `Dockerfile` | Imagem da API (python:3.11-slim + uv) |
| `docker-compose.yml` | valen-api + postgres + redis + qdrant + minio |
| `.env.example` | Template de variáveis de ambiente |
| `.gitignore` | Ignora venv, .env, caches, dados locais |
| `README.md` | Visão geral e quickstart |
| `PROJECT.md` | Fonte da verdade arquitetural |
| `CHANGELOG.md` | Histórico (Keep a Changelog) |
| `setup.sh` / `update.sh` / `backup.sh` | Scripts operacionais |

### Pacote `valen/` (arquitetura DDD em camadas)

```
valen/
├── __init__.py          # __version__ = "1.0.0"
├── main.py              # FastAPI app + /health  (stub)
├── config.py            # Settings via pydantic-settings
├── domains/
│   ├── agents/          # entities, value_objects, repositories, services, events, commands
│   ├── memory/          # entities, repositories, services
│   ├── tools/           # base.py, sandbox.py, acl.py, audit.py + implementations/
│   ├── providers/       # base.py (ABC) + groq/ollama/anthropic/openai/registry
│   └── observability/   # metrics, tracing, logging
├── infrastructure/
│   ├── database/        # postgres, redis, qdrant, minio
│   └── migrations/      # 001_initial.sql
├── application/         # commands/ + queries/  (CQRS)
└── interfaces/
    ├── api/             # routes/ + websocket/
    └── cli/             # commands.py
tests/
├── unit/tools/
└── integration/tools/
```

### Estado dos módulos (Fase 0)

- **Com esqueleto definido** (shape/contratos, corpo `...`):
  `tools/base.py`, `tools/sandbox.py`, `tools/acl.py`, `tools/audit.py`,
  `providers/base.py`, `config.py`, `main.py`.
- **Stubs leves** (docstring + marcador de fase): demais implementations, providers,
  observability, database, cli.
- **Pacotes vazios** (`__init__.py`): entities, value_objects, repositories, services,
  events, commands das camadas agents/memory/application.

Nenhuma lógica da Fase 1+ foi implementada. Os esqueletos só fixam interfaces.

---

## 3. Plano de implementação fase a fase

### Fase 1 — Sistema de Tools + Sandbox + ACL + Audit Trail  *(próxima)*
1. `ToolBase` / `ToolResult` / `ToolContext` completos.
2. `Sandbox`: enforcement dos Execution Tiers + checagem `ALWAYS_BLOCKED` (regex).
3. `ACL`: validação de `AGENT_PERMISSIONS` por agente/ação.
4. `AuditTrail` imutável com hashing (sha256 de args) → tabela `audit_trail`.
5. `FilesystemTool`, `TerminalTool`, `MemoryTool`.
6. Testes cobrindo todos os tiers e sandbox modes.
**Gate:** testes verdes antes da Fase 2.

### Fase 2 — NeuroValen
- `Note`/`NoteLink` entities, `IMemoryRepository`, `MemorySearchService`.
- Notas Markdown + frontmatter; busca híbrida Qdrant (semântica) + PostgreSQL FTS.
- `MemoryTool` ligada ao NeuroValen. Backups via Nexus.

### Fase 3 — Os 4 Agentes
- `Agent`, `AgentState`, `AgentMessage`; `AgentOrchestrationService`.
- CEO, Forge, Nexus, Analyst — acessando o mundo **só** via Tools.
- Eventos: AgentStarted/Failed/Completed. Commands: Run/Stop.

### Fase 4 — Providers + comunicação inter-agentes
- `GroqProvider`, `OllamaProvider` reais; stubs Anthropic/OpenAI ativáveis.
- `ProviderRegistry` com fallback por prioridade; retry + backoff exponencial.
- Pub/sub entre agentes via Redis. Nexus monitora latência/saúde.

### Fase 5 — API + WebSocket + interface visual
- Routers FastAPI, handlers WebSocket, núcleo neural visual.

### Fase 6 — Testes, docs, release
- Cobertura ampla, documentação, carimbar 1.0.0 em tudo.

---

## 4. Dependências e riscos identificados

### Ambiente
- **Python 3.11+ exigido; host tem 3.10.12.** Mitigação: `uv` provê o Python 3.11
  do projeto (`uv sync` / `uv python install`), sem tocar o Python do sistema.
- `uv` não estava instalado — instalado na Fase 0 (`setup.sh` também cobre).
- `docker` presente; infraestrutura (postgres/redis/qdrant/minio) sobe via compose.

### Riscos técnicos
- **Busca híbrida (Fase 2):** sincronizar Qdrant ↔ PostgreSQL FTS; risco de
  divergência entre índices. Definir fonte da verdade e estratégia de reindex.
- **Sandbox/TerminalTool (Fase 1):** `ALWAYS_BLOCKED` por regex pode ter bypass via
  encoding/aliases. Validar normalização do comando antes do match. **Crítico:** é a
  superfície de maior risco de segurança do sistema.
- **Audit Trail imutável:** garantir append-only no nível de permissões do banco
  (sem GRANT de UPDATE/DELETE para o usuário da app), não só na aplicação.
- **Fallback de providers:** evitar loops de retry e mascarar falhas; logar cada
  tentativa e respeitar timeouts.
- **Volume de dev no compose** (`./valen:/app/valen`) é prático em dev, mas a imagem
  já copia `valen/` — alinhar antes de produção.

### Versão obsoleta no compose
- Removida a chave `version:` do `docker-compose.yml` (obsoleta no Compose v2).

---

## 5. Próximo passo

Fase 0 concluída. **Aguardando validação do usuário** antes de iniciar a Fase 1
(Sistema de Tools + Sandbox + ACL + Audit Trail).
