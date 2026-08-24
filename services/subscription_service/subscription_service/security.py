"""JWT: идентификация через Telegram, авторизация запросов по Bearer-токену."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from .db import get_session
from .models import User

_bearer = HTTPBearer(auto_error=False)


def create_token(user_id: str, secret: str, ttl_hours: int) -> str:
    payload = {"sub": user_id, "exp": datetime.now(UTC) + timedelta(hours=ttl_hours)}
    return jwt.encode(payload, secret, algorithm="HS256")


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    session: AsyncSession = Depends(get_session),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    settings = request.app.state.settings
    try:
        payload = jwt.decode(credentials.credentials, settings.jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc
    user = await session.get(User, payload.get("sub"))
    if user is None:
        raise HTTPException(status_code=401, detail="Unknown user")
    return user
