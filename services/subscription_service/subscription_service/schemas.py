from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class TelegramAuthRequest(BaseModel):
    # TODO(Phase 1): полная схема Telegram Login Widget + проверка hash подписи бота.
    telegram_id: int
    username: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str


class SubscriptionCreate(BaseModel):
    fight_id: str
    lead_time_min: int = Field(default=15, ge=1, le=240)
    channel: str = "telegram"


class SubscriptionOut(BaseModel):
    id: str
    fight_id: str
    lead_time_min: int
    channel: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class FightOut(BaseModel):
    id: str
    order_no: int
    segment: str
    fighter_red: str
    fighter_blue: str
    scheduled_rounds: int


class CardOut(BaseModel):
    event_id: str
    name: str
    scheduled_start: datetime
    fights: list[FightOut]
