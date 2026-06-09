# VALEN v1.0.0

Plataforma autônoma de desenvolvimento e vida pessoal.
Criado por **Astraz Studio**. Cérebro central: **NeuroValen**.

---

## O que é

VALEN é um sistema multi-agente autônomo construído sobre um **sistema de Tools com
Sandbox** como pilar central. Nenhuma ação acontece fora desse sistema: todo acesso a
arquivos, shell, rede, memória e providers de IA passa por uma `ToolBase` com
classificação de risco, ACL por agente e Audit Trail imutável.

## Os 4 Agentes (regra absoluta)

| Agente | Símbolo | Papel |
|--------|---------|-------|
| CEO | ♛ | Interface principal e orquestrador. Personalidade Jarvis + Tony Stark. |
| Forge | ⚒ | Criação de código, projetos e scripts. |
| Nexus | ⬢ | Infraestrutura, Docker, monitoramento, backups. |
| Analyst | ◇ | Análise profunda, relatórios, raciocínio estratégico. |

**Regra R2:** qualquer "agente" além desses 4 vira Tool ou Service. Nunca agente.

## Stack

- **Backend:** Python 3.11+, FastAPI (REST + WebSocket), Pydantic v2
- **Dados:** PostgreSQL 16, Redis 7, Qdrant (vetorial), MinIO (object storage)
- **Providers IA:** Groq (prioritário), Ollama (local); Anthropic/OpenAI/Gemini/Grok modulares
- **Observabilidade:** Prometheus + Grafana + OpenTelemetry + Sentry
- **Runtime:** Docker + Docker Compose · **Deps:** `uv`

## Ambiente

- Servidor: Oracle Cloud Free Tier (Ubuntu 22.04 LTS x86_64)
- Acesso remoto: SSH via Termux (apenas cliente)
- Sessões persistentes: tmux

## Quickstart (dev)

```bash
cp .env.example .env          # preencha os segredos
uv sync                       # instala dependências (Python 3.11+)
docker compose up -d          # sobe postgres, redis, qdrant, minio, api
curl http://localhost:8000/health
```

## Estrutura

Arquitetura em camadas (DDD): `domains/` (agents, memory, tools, providers,
observability), `infrastructure/` (database, migrations), `application/` (CQRS),
`interfaces/` (api, cli). Detalhe completo em [`PROJECT.md`](./PROJECT.md).

## Rodar sem Docker (dev rápido)

VALEN roda 100% sem infraestrutura externa (memória in-process + MockProvider):

```bash
uv sync --extra dev
uv run valen status          # agentes, tools, providers
uv run valen chat CEO "olá?" # conversa via CLI
uv run valen serve           # API em http://localhost:8000  (UI em /)
uv run pytest -q             # 56 testes
```

Com `GROQ_API_KEY` no ambiente, o GroqProvider entra automaticamente à frente do mock.

## Status

**Fases 0–6 concluídas** — sistema funcional end-to-end: Tools+Sandbox+ACL+Audit,
NeuroValen, 4 agentes, providers com fallback, API+WebSocket+CLI, observability.
56 testes verdes, imagem Docker validada. Detalhes em
[`VALEN_v1.0.0_REFACTOR_PLAN.md`](./VALEN_v1.0.0_REFACTOR_PLAN.md) e
[`CHANGELOG.md`](./CHANGELOG.md).

---

*Astraz Studio · Junho 2026*
