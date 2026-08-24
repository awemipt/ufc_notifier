from __future__ import annotations

from ufc_common.settings import BaseServiceSettings


class Settings(BaseServiceSettings):
    service_name: str = "subscription-service"
    database_url: str = "sqlite+aiosqlite:///./subscription.db"
    jwt_secret: str = "dev-secret-change-me"  # в проде — из секрета (задание 05-k8s)
    jwt_ttl_hours: int = 72
    # Phase 0: кард читается из файла симулятора. Phase 1: proxy к schedule_engine API.
    card_file: str = "simulator-data/ufc_fight_night_sample.json"
