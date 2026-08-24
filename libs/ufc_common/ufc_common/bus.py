"""Абстракция событийной шины.

Phase 0: InMemoryBus — синхронная in-process доставка (демо и тесты).
Phase 1: KafkaBus (aiokafka) — появится после того, как владелец проекта поднимет
Kafka по заданию devops-tasks/02-compose.md; интерфейс не изменится.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable

from pydantic import BaseModel

Handler = Callable[[str | None, BaseModel], Awaitable[None]]


class EventBus(ABC):
    @abstractmethod
    async def publish(self, topic: str, key: str | None, event: BaseModel) -> None: ...

    @abstractmethod
    def subscribe(self, topic: str, handler: Handler) -> None: ...


class InMemoryBus(EventBus):
    """Доставляет события подписчикам немедленно и последовательно (детерминизм)."""

    def __init__(self) -> None:
        self._handlers: dict[str, list[Handler]] = {}
        self.published: list[tuple[str, str | None, BaseModel]] = []

    async def publish(self, topic: str, key: str | None, event: BaseModel) -> None:
        self.published.append((topic, key, event))
        for handler in self._handlers.get(topic, []):
            await handler(key, event)

    def subscribe(self, topic: str, handler: Handler) -> None:
        self._handlers.setdefault(topic, []).append(handler)


class KafkaBus(EventBus):
    """Появится в Phase 1 (см. devops-tasks/02-compose.md — Kafka должна быть поднята)."""

    def __init__(self, bootstrap_servers: str) -> None:
        raise NotImplementedError(
            "KafkaBus реализуется в Phase 1, когда будет выполнено задание "
            "devops-tasks/02-compose.md (Kafka в docker-compose)."
        )

    async def publish(self, topic: str, key: str | None, event: BaseModel) -> None:
        raise NotImplementedError

    def subscribe(self, topic: str, handler: Handler) -> None:
        raise NotImplementedError
