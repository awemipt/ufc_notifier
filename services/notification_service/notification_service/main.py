"""Скелет сервиса. Phase 1: consumer-циклы Kafka (fight-eta.v1, subscription-events.v1),
таблица deliveries, ретраи, DLQ, TelegramChannel. Пока сервис живёт в in-process демо
(scripts/dev_run_pipeline.py)."""

from __future__ import annotations

from fastapi import FastAPI
from ufc_common.health import health_router


def create_app() -> FastAPI:
    app = FastAPI(title="UFC Notifier — notification service")
    app.include_router(health_router())
    return app
