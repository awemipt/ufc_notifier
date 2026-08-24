"""Идентификация через Telegram + выдача JWT.

Phase 0: доверяем telegram_id из тела запроса (для демо и тестов).
TODO(Phase 1): проверка hash-подписи Telegram Login Widget / deep-link токена бота.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..models import User
from ..schemas import TelegramAuthRequest, TokenResponse
from ..security import create_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/telegram", response_model=TokenResponse)
async def auth_telegram(
    body: TelegramAuthRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> TokenResponse:
    user = (
        await session.execute(select(User).where(User.telegram_id == body.telegram_id))
    ).scalar_one_or_none()
    if user is None:
        user = User(telegram_id=body.telegram_id, username=body.username)
        session.add(user)
    elif body.username and user.username != body.username:
        user.username = body.username
    await session.commit()

    settings = request.app.state.settings
    token = create_token(user.id, settings.jwt_secret, settings.jwt_ttl_hours)
    return TokenResponse(access_token=token, user_id=user.id)
