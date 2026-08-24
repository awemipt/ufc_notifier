"""Канал-заглушка: печатает уведомление. Позволяет гонять весь пайплайн до Telegram."""

from __future__ import annotations

from ufc_common.events import NotificationRequest
from ufc_common.logging import get_logger

from .base import NotificationChannel

log = get_logger(__name__)


class LogChannel(NotificationChannel):
    name = "log"

    def __init__(self) -> None:
        self.sent: list[NotificationRequest] = []

    async def send(self, request: NotificationRequest) -> None:
        self.sent.append(request)
        log.info(
            "notification delivered",
            user=request.user_label or request.user_id,
            fight_id=request.fight_id,
            message=request.message,
        )
