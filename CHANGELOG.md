# Changelog

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/).
Versionamento [SemVer](https://semver.org/lang/pt-BR/).

## [Unreleased]

### Fase 0 — Estrutura do projeto (2026-06-09)

#### Added
- Estrutura de pastas completa (DDD: domains, infrastructure, application, interfaces).
- Arquivos base: `pyproject.toml`, `Dockerfile`, `docker-compose.yml`, `.env.example`,
  `.gitignore`, `README.md`, `PROJECT.md`, `CHANGELOG.md`.
- Scripts: `setup.sh`, `update.sh`, `backup.sh`.
- Schema SQL inicial: `valen/infrastructure/migrations/001_initial.sql`
  (Event Store, Audit Trail, NeuroValen notes, sessions, plugins).
- Stubs de todos os módulos (tools, providers, observability, infraestrutura, interfaces).
- `VALEN_v1.0.0_REFACTOR_PLAN.md` com plano fase a fase.

#### Notes
- Repositório iniciado do zero. Nenhum código antigo a preservar ou migrar.

### Fases 1–6 — Sistema funcional end-to-end (2026-06-09)

#### Added
- **Fase 1 — Tools + Sandbox + ACL + Audit Trail:** `ToolBase.execute` orquestra
  ACL → ALWAYS_BLOCKED → tier/aprovação → dry-run → timeout → auditoria.
  `Sandbox` (classificação de tier + 22 padrões bloqueados), `ACL` por agente,
  `AuditTrail` imutável com hash (sink in-memory + Postgres). FilesystemTool,
  TerminalTool, NetworkTool, ProviderTool.
- **Fase 2 — NeuroValen:** `Note`/`NoteLink`, repositório in-memory, busca híbrida
  (ranking lexical título>tags>conteúdo + boost de prioridade), `MemoryTool`.
- **Fase 3 — 4 Agentes:** CEO/Forge/Nexus/Analyst com personas, sandbox e tools;
  `AgentOrchestrationService` (chat + use_tool, acesso ao mundo só via Tools).
- **Fase 4 — Providers:** GroqProvider, OllamaProvider, MockProvider; `ProviderRegistry`
  com fallback por prioridade + retry/backoff (roda sem API key via mock).
- **Fase 5 — Interfaces:** FastAPI (health, status, agents, memory, metrics),
  WebSocket `/ws/chat`, UI neural em `/`, CLI typer (`valen status|agents|chat|serve`).
- **Fase 6 — Observability + validação:** logging JSON (structlog), métricas
  Prometheus, tracing OTEL no-op. Kernel de montagem central.

#### Quality
- 56 testes verdes (unit + integração API/WS). Ruff limpo. Imagem Docker build OK,
  container serve `/health`, `/status`, `/metrics`.
