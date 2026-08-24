"""Контракты событий шины. Единственный источник правды — см. docs/events.md.

Изменение схемы = новая versioned-модель и новый топик (*.v2), старые не ломаем.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

TOPIC_FIGHT_EVENTS = "fight-events.v1"
TOPIC_FIGHT_ETA = "fight-eta.v1"
TOPIC_SUBSCRIPTION_EVENTS = "subscription-events.v1"
TOPIC_NOTIFICATION_REQUESTS = "notification-requests.v1"
TOPIC_NOTIFICATION_DLQ = "notification-requests.dlq.v1"


class CardSegment(StrEnum):
    EARLY_PRELIMS = "early_prelims"
    PRELIMS = "prelims"
    MAIN_CARD = "main_card"


class FightEventType(StrEnum):
    EVENT_STARTED = "EVENT_STARTED"
    FIGHT_STARTED = "FIGHT_STARTED"
    FIGHT_FINISHED = "FIGHT_FINISHED"
    FIGHT_CANCELLED = "FIGHT_CANCELLED"
    CARD_UPDATED = "CARD_UPDATED"


class EtaConfidence(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class BusEvent(BaseModel):
    schema_version: int = 1
    occurred_at: datetime


class FightEvent(BusEvent):
    type: FightEventType
    event_id: str
    fight_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)

    @property
    def key(self) -> str:
        return self.fight_id or self.event_id


class EtaUpdate(BusEvent):
    event_id: str
    fight_id: str
    eta_start: datetime
    confidence: EtaConfidence
    computed_at: datetime


class SubscriptionEventType(StrEnum):
    CREATED = "CREATED"
    CANCELLED = "CANCELLED"


class SubscriptionEvent(BusEvent):
    type: SubscriptionEventType
    subscription_id: str
    user_id: str
    fight_id: str
    lead_time_min: int = 15
    channel: str = "telegram"
    telegram_chat_id: int | None = None
    user_label: str | None = None


class NotificationRequest(BusEvent):
    subscription_id: str
    user_id: str
    fight_id: str
    channel: str
    eta_start: datetime
    fire_at: datetime
    message: str
    user_label: str | None = None
    telegram_chat_id: int | None = None
