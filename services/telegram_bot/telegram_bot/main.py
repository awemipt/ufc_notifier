"""Скелет бота. Phase 1: aiogram 3 в webhook-режиме за gateway (/tg/webhook),
диалоги в handlers/, REST-клиент к subscription_service (api_client.py)."""

from __future__ import annotations

from fastapi import FastAPI
from ufc_common.health import health_router


def create_app() -> FastAPI:
    app = FastAPI(title="UFC Notifier — telegram bot")
    app.include_router(health_router())
    return app
