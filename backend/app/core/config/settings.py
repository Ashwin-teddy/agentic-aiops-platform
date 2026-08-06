from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "agentic-aiops-platform"
    app_version: str = "1.0.0"
    app_env: Literal["development", "staging", "production"] = "development"
    app_debug: bool = False
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_secret_key: str = Field(..., min_length=16)
    app_workers: int = 4

    database_url: str = Field(..., description="PostgreSQL async connection string")
    database_pool_size: int = 20
    database_max_overflow: int = 10

    redis_url: str = "redis://localhost:6379/0"
    redis_password: str = ""
    redis_max_connections: int = 50

    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "aiops_knowledge"
    qdrant_api_key: str = ""

    openai_api_key: str = Field(default="", description="OpenAI API key")
    openai_org_id: str = ""
    openai_embedding_model: str = "text-embedding-3-large"
    openai_chat_model: str = "gpt-4o"
    openai_embedding_dims: int = 3072

    anthropic_api_key: str = ""
    google_api_key: str = ""
    cohere_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434"

    google_oauth_client_id: str = ""
    google_oauth_client_secret: str = ""
    google_oauth_redirect_uri: str = ""

    default_chat_model: str = "llama3.2"
    default_embedding_model: str = "nomic-embed-text"
    default_intent_model: str = "llama3.2"
    default_planning_model: str = "llama3.2"
    default_troubleshooting_model: str = "llama3.2"
    default_rag_model: str = "llama3.2"
    llm_fallback_enabled: bool = True

    jwt_secret_key: str = Field(..., min_length=16)
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    azure_ad_tenant_id: str = ""
    azure_ad_client_id: str = ""
    azure_ad_client_secret: str = ""
    azure_ad_redirect_uri: str = "http://localhost:8000/auth/callback"

    okta_domain: str = ""
    okta_client_id: str = ""
    okta_client_secret: str = ""

    servicenow_url: str = ""
    servicenow_username: str = ""
    servicenow_password: str = ""

    jira_url: str = ""
    jira_username: str = ""
    jira_api_token: str = ""

    github_token: str = ""
    github_org: str = ""

    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "us-east-1"

    kubeconfig_path: str = "~/.kube/config"
    k8s_in_cluster: bool = False

    slack_bot_token: str = ""
    slack_signing_secret: str = ""

    teams_tenant_id: str = ""
    teams_client_id: str = ""
    teams_client_secret: str = ""

    smtp_host: str = "smtp.office365.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from: str = ""

    otel_exporter_otlp_endpoint: str = "http://localhost:4317"
    otel_service_name: str = "agentic-aiops"
    otel_environment: str = "development"
    prometheus_port: int = 9090

    encryption_key: str = Field(..., min_length=32)
    rate_limit_per_minute: int = 100
    cors_origins: list[str] = ["http://localhost:3000"]

    llm_temperature: float = 0.1
    llm_max_tokens: int = 4096
    llm_timeout: int = 60
    rag_top_k: int = 5
    rag_similarity_threshold: float = 0.75

    auto_approve_threshold: float = 0.3
    high_risk_threshold: float = 0.7
    critical_risk_threshold: float = 0.9

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            import json
            return json.loads(v)
        return v

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def sync_database_url(self) -> str:
        return self.database_url.replace("+asyncpg", "")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
