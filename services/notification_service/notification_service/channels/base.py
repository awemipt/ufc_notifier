"""Контракт канала доставки. Реализации: LogChannel (Phase 0), Telegram (Phase 1),
робозвонок/SMS/email (Phase 4)."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ufc_common.events import NotificationRequest


class NotificationChannel(ABC):
    name: str

    @abstractmethod
    async def send(self, request: NotificationRequest) -> None:
        """Бросает исключение при неудаче — ретраи и DLQ решает вызывающий (Phase 1)."""
        ...
