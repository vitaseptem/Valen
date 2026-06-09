"""Configuração central do VALEN via Pydantic Settings.

Carrega variáveis de ambiente (ver `.env.example`). Stub da Fase 0: define o
shape das configs; validações e parsing avançado entram nas fases seguintes.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações da aplicação, lidas do ambiente / arquivo .env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Identidade
    valen_env: str = "development"
    valen_version: str = "1.0.0"
    valen_log_level: str = "INFO"
    valen_autonomy_level: int = 5

    # Bancos de dados
    postgres_url: str = "postgresql://valen:password@localhost:5432/valen"
    redis_url: str = "redis://:password@localhost:6379/0"
    qdrant_url: str = "http://localhost:6333"
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "valen_admin"
    minio_secret_key: str = "change_me_in_production"
    minio_secure: bool = False

    # Providers de IA
    valen_default_provider: str = "groq"
    valen_fallback_providers: str = "ollama,anthropic"
    groq_api_key: str = ""
    ollama_url: str = "http://localhost:11434"
    anthropic_api_key: str = ""
    openai_api_key: str = ""

    # Segurança / observabilidade
    valen_secret_key: str = "change_me_32_chars_minimum"
    sentry_dsn: str = ""


def get_settings() -> Settings:
    """Retorna as configurações carregadas do ambiente."""
    return Settings()
