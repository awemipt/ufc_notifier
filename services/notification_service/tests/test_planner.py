from datetime import UTC, datetime, timedelta

from notification_service.planner import NotificationPlanner
from ufc_common.events import (
    EtaConfidence,
    EtaUpdate,
    SubscriptionEvent,
    SubscriptionEventType,
)

T0 = datetime(2026, 8, 29, 22, 0, tzinfo=UTC)


def sub_event(
    sub_id: str = "s1",
    fight_id: str = "f05",
    lead: int = 10,
    type_: SubscriptionEventType = SubscriptionEventType.CREATED,
) -> SubscriptionEvent:
    return SubscriptionEvent(
        type=type_,
        subscription_id=sub_id,
        user_id="u1",
        fight_id=fight_id,
        lead_time_min=lead,
        telegram_chat_id=111,
        user_label="alice",
        occurred_at=T0,
    )


def eta(fight_id: str = "f05", minutes_from_t0: float = 60) -> EtaUpdate:
    return EtaUpdate(
        event_id="ev1",
        fight_id=fight_id,
        eta_start=T0 + timedelta(minutes=minutes_from_t0),
        confidence=EtaConfidence.HIGH,
        computed_at=T0,
        occurred_at=T0,
    )


async def test_notification_fires_at_eta_minus_lead_time():
    planner = NotificationPlanner()
    await planner.handle_subscription_event(None, sub_event(lead=10))
    await planner.handle_eta_update(None, eta(minutes_from_t0=60))  # ETA 23:00

    assert planner.due(T0 + timedelta(minutes=49)) == []  # 22:49 — рано
    fired = planner.due(T0 + timedelta(minutes=50))  # 22:50 = ETA − lead
    assert len(fired) == 1
    assert fired[0].fire_at == T0 + timedelta(minutes=50)
    assert "23:00" in fired[0].message


async def test_notification_is_sent_exactly_once():
    planner = NotificationPlanner()
    await planner.handle_subscription_event(None, sub_event())
    await planner.handle_eta_update(None, eta())
    late = T0 + timedelta(minutes=55)
    assert len(planner.due(late)) == 1
    assert planner.due(late) == []
    assert planner.due(late + timedelta(minutes=5)) == []


async def test_cancelled_subscription_never_fires():
    planner = NotificationPlanner()
    await planner.handle_subscription_event(None, sub_event())
    await planner.handle_eta_update(None, eta())
    await planner.handle_subscription_event(
        None, sub_event(type_=SubscriptionEventType.CANCELLED)
    )
    assert planner.due(T0 + timedelta(hours=2)) == []


async def test_eta_shift_earlier_moves_fire_time():
    planner = NotificationPlanner()
    await planner.handle_subscription_event(None, sub_event(lead=10))
    await planner.handle_eta_update(None, eta(minutes_from_t0=60))
    # Быстрые нокауты: ETA сдвинулся на 22:40 — уведомление должно уйти уже в 22:30.
    await planner.handle_eta_update(None, eta(minutes_from_t0=40))
    assert len(planner.due(T0 + timedelta(minutes=30))) == 1


async def test_without_eta_nothing_fires():
    planner = NotificationPlanner()
    await planner.handle_subscription_event(None, sub_event())
    assert planner.due(T0 + timedelta(hours=3)) == []


async def test_multiple_subscribers_sorted_by_fire_time():
    planner = NotificationPlanner()
    await planner.handle_subscription_event(None, sub_event("s1", "f05", lead=10))
    await planner.handle_subscription_event(None, sub_event("s2", "f05", lead=30))
    await planner.handle_eta_update(None, eta())
    fired = planner.due(T0 + timedelta(minutes=55))
    assert [r.subscription_id for r in fired] == ["s2", "s1"]  # больший lead — раньше
