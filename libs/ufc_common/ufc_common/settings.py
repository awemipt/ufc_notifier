"""Базовые настройки сервиса: конфиг только из env (12-factor)."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseServiceSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "service"
    log_level: str = "INFO"
    log_json: bool = True
    # Пусто → InMemoryBus. Появится Kafka (Phase 1) → адрес брокера включит KafkaBus.
    kafka_bootstrap_servers: str = ""
