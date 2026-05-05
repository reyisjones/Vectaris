"""Application configuration loaded from environment variables.

All settings are pulled from a `.env` file or process environment using
pydantic-settings. Values are read once at import time via `settings`.
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # --- Application ---
    app_name: str = "AI Platform Dashboard"
    environment: str = "development"
    log_level: str = "INFO"
    api_version: str = "1.0.0"

    # --- HTTP / CORS ---
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:5173"]
    )
    request_timeout_seconds: float = 10.0

    # --- Auth ---
    # Static API key mode: when non-empty, requests must carry X-API-Key with this value.
    api_key: str = ""
    api_key_header: str = "X-API-Key"

    # OIDC mode: when oidc_issuer is set, Bearer JWT validation replaces the static key.
    # Set oidc_jwks_uri to skip discovery (faster startup); leave empty to auto-discover.
    # Azure AD example: https://login.microsoftonline.com/{tenant}/v2.0
    oidc_issuer: str = ""
    oidc_audience: str = ""
    oidc_jwks_uri: str = ""

    # --- OpenTelemetry ---
    otel_enabled: bool = False
    otel_service_name: str = "ai-platform-dashboard"
    otel_exporter_otlp_endpoint: str = "http://localhost:4317"

    # --- Azure Monitor (optional) ---
    azure_monitor_connection_string: str = ""

    # --- Ollama / local LLM runtime ---
    ollama_enabled: bool = False
    ollama_base_url: str = "http://localhost:11434"

    # --- Polling / refresh ---
    metrics_refresh_seconds: int = 30


settings = Settings()
