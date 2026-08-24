from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ufc_common.events import (
    TOPIC_SUBSCRIPTION_EVENTS,
    SubscriptionEvent,
    SubscriptionEventType,
)

from ..db import get_session
from ..models import Subscription, User
from ..schemas import SubscriptionCreate, SubscriptionOut
from ..security import get_current_user

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


async def _publish(request: Request, sub: Subscription, user: User,
                   type_: SubscriptionEventType) -> None:
    event = SubscriptionEvent(
        type=type_,
        subscription_id=sub.id,
        user_id=user.id,
        fight_id=sub.fight_id,
        lead_time_min=sub.lead_time_min,
        channel=sub.channel,
        telegram_chat_id=user.telegram_id,
        user_label=user.username,
        occurred_at=datetime.now(UTC),
    )
    await request.app.state.bus.publish(TOPIC_SUBSCRIPTION_EVENTS, sub.id, event)


@router.get("", response_model=list[SubscriptionOut])
async def list_subscriptions(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[Subscription]:
    result = await session.execute(
        select(Subscription).where(
            Subscription.user_id == user.id, Subscription.status == "active"
        )
    )
    return list(result.scalars())


@router.post("", response_model=SubscriptionOut, status_code=201)
async def create_subscription(
    body: SubscriptionCreate,
    request: Request,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Subscription:
    existing = (
        await session.execute(
            select(Subscription).where(
                Subscription.user_id == user.id,
                Subscription.fight_id == body.fight_id,
                Subscription.channel == body.channel,
                Subscription.status == "active",
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=409, detail="Already subscribed to this fight")

    sub = Subscription(
        user_id=user.id,
        fight_id=body.fight_id,
        lead_time_min=body.lead_time_min,
        channel=body.channel,
    )
    session.add(sub)
    await session.commit()
    await _publish(request, sub, user, SubscriptionEventType.CREATED)
    return sub


@router.delete("/{subscription_id}", status_code=204)
async def cancel_subscription(
    subscription_id: str,
    request: Request,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Response:
    sub = await session.get(Subscription, subscription_id)
    if sub is None or sub.user_id != user.id or sub.status != "active":
        raise HTTPException(status_code=404, detail="Subscription not found")
    sub.status = "cancelled"
    await session.commit()
    await _publish(request, sub, user, SubscriptionEventType.CANCELLED)
    return Response(status_code=204)
