# PROJECT.md — VALEN v1.0.0

Documento de arquitetura. Fonte da verdade técnica do projeto.

---

## Identidade

- **Nome:** VALEN · **Versão:** 1.0.0 · **Autor:** Astraz Studio
- **Cérebro central:** NeuroValen · **Data:** Junho 2026

## Princípios inquebráveis

- **R1 — Tools são o pilar:** nada acontece fora do sistema de Tools + Sandbox.
- **R2 — 4 agentes apenas:** CEO, Forge, Nexus, Analyst. Qualquer outro vira Tool/Service.
- **Sem shell direto:** agentes nunca executam shell no próprio código — sempre via `ToolBase`.
- **Imutabilidade:** Event Store e Audit Trail são append-only. Nunca UPDATE/DELETE.
- **Simples > elegante quebrado.** Sem complexidade desnecessária.
- **Fases em ordem.** Não pular etapas nem testes.

## Arquitetura em camadas (DDD)

```
interfaces/      API REST, WebSocket, CLI  (entrada/saída)
application/     CQRS: command + query handlers
domains/         núcleo: agents, memory, tools, providers, observability
infrastructure/  database (postgres/redis/qdrant/minio), migrations
```

## Sistema de Tools + Sandbox

Base: `ToolBase` / `ToolResult` / `ToolContext` (ver `domains/tools/base.py`).

### Execution Tiers

| Tier | Exemplos | Aprovação |
|------|----------|-----------|
| `READ_ONLY` | ls, cat, ps, df, curl GET | Não |
| `REVERSIBLE` | mkdir, cp, echo, curl POST | Não (dry-run padrão) |
| `DESTRUCTIVE` | rm, mv, sed -i, truncate | Sim, sempre |
| `SYSTEM_LEVEL` | systemctl, docker, apt, kill | Sim, sempre |

### Sandbox Modes

| Modo | Quem usa | Restrição |
|------|----------|-----------|
| `safe` | Forge, Analyst | Máxima |
| `restricted` | CEO | Alta |
| `docker` | Nexus | Máxima + isolamento de rede |
| `unrestricted` | CEO c/ aprovação documentada | Nenhuma |

### ACL por agente

```python
AGENT_PERMISSIONS = {
    "CEO":     {"read", "write", "execute", "network", "memory", "docker_inspect"},
    "Forge":   {"read", "write", "execute", "memory"},
    "Nexus":   {"read", "write", "execute", "network", "docker_full", "memory", "system_monitor"},
    "Analyst": {"read", "memory", "network_read"},
}
```

`ALWAYS_BLOCKED`: padrões nunca executados (rm -rf /, dd, mkfs, reboot, sudo, chmod 777…).
Lista completa em `domains/tools/sandbox.py`.

### Tools obrigatórias v1.0.0

| Tool | Responsabilidade | Tier máx | Agente |
|------|------------------|----------|--------|
| FilesystemTool | Leitura/escrita de arquivos | DESTRUCTIVE | Forge |
| TerminalTool | Shell com Sandbox | SYSTEM_LEVEL | Forge, Nexus |
| MemoryTool | NeuroValen | REVERSIBLE | Todos |
| NetworkTool | HTTP / monitoramento | REVERSIBLE | Nexus, CEO |
| DockerTool | Containers | SYSTEM_LEVEL | Nexus |
| ProviderTool | LLMs externos | REVERSIBLE | Todos |
| BrowserTool | Navegação/scraping | REVERSIBLE | CEO, Forge |
| VisionTool | Análise de imagens | READ_ONLY | CEO, Analyst |
| EventTool | Lembretes/agendamentos | REVERSIBLE | CEO |

### Audit Trail (entrada por execução)

`timestamp, agent_id, tool_name, action, args_hash, tier, sandbox_mode, dry_run,
result_ok, duration_ms, audit_hash`. Persistido em `audit_trail` (append-only).

## NeuroValen — cérebro central

- Único repositório de memória de longo prazo. Acesso só via `MemoryTool`.
- Notas Markdown + frontmatter semântico (type, tags, created, priority).
- Busca híbrida: semântica (Qdrant) + full-text (PostgreSQL FTS).
- Backups automáticos gerenciados pelo Nexus.

## Providers de IA

`ProviderBase` (ABC) com `complete()` e `stream()`. Implementar nesta ordem:
1. **GroqProvider** — `llama3-70b-8192`, `mixtral-8x7b-32768`
2. **OllamaProvider** — local, endpoint configurável
3. Anthropic / OpenAI / Gemini / Grok — stubs prontos para ativar.

Fallback automático: provider padrão via `.env`; se falhar, tenta próximo na lista.
Nexus monitora latência e saúde em tempo real.

## Persistência (PostgreSQL)

Tabelas: `domain_events` (Event Store), `audit_trail`, `neurovalen_notes`,
`agent_sessions`, `installed_plugins`. Schema em
`valen/infrastructure/migrations/001_initial.sql`.

## Qualidade exigida (não negociável)

Type hints completos · Pydantic v2 · async/await em todo I/O · logging JSON
(structlog) · timeouts em ops externas · retry com backoff exponencial · docstrings
públicas · testes do sistema de Tools antes da Fase 1 fechar.

## Fases

| Fase | Entrega | Gate |
|------|---------|------|
| 0 | Estrutura + plano de refatoração | ✅ |
| 1 | Tools + Sandbox + ACL + Audit Trail | ✅ |
| 2 | NeuroValen (notas, busca híbrida, MemoryTool) | ✅ |
| 3 | Os 4 agentes usando só Tools | ✅ |
| 4 | Providers (Groq + Ollama) + comunicação inter-agentes | ✅ |
| 5 | FastAPI + WebSocket + interface visual (núcleo neural) | ✅ |
| 6 | Testes, docs, 1.0.0 em tudo | entrega final |
