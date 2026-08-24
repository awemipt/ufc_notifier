"""Интеграция ScheduleEngine с шиной: применение событий, noise gate, confidence."""

from datetime import datetime

from schedule_engine.engine import ScheduleEngine
from schedule_engine.models import FightStatus
from schedule_engine.testing import T0, make_card, mins
from ufc_common.bus import InMemoryBus
from ufc_common.events import (
    TOPIC_FIGHT_ETA,
    EtaConfidence,
    EtaUpdate,
    FightEvent,
    FightEventType,
)


def fight_event(type_: FightEventType, at: datetime, fight_id: str | None = None) -> FightEvent:
    return FightEvent(type=type_, event_id="ev1", fight_id=fight_id, occurred_at=at)


def eta_updates(bus: InMemoryBus, fight_id: str | None = None) -> list[EtaUpdate]:
    return [
        ev
        for topic, _key, ev in bus.published
        if topic == TOPIC_FIGHT_ETA and (fight_id is None or ev.fight_id == fight_id)
    ]


async def make_engine() -> tuple[ScheduleEngine, InMemoryBus]:
    bus = InMemoryBus()
    engine = ScheduleEngine(bus, make_card())
    await engine.handle_fight_event(None, fight_event(FightEventType.EVENT_STARTED, T0))
    return engine, bus


async def test_event_started_publishes_initial_etas_with_confidence_gradient():
    _engine, bus = await make_engine()
    updates = eta_updates(bus)
    assert [u.fight_id for u in updates] == ["f1", "f2", "f3", "f4", "f5"]
    assert [u.confidence for u in updates] == [
        EtaConfidence.HIGH,
        EtaConfidence.MEDIUM,
        EtaConfidence.MEDIUM,
        EtaConfidence.LOW,
        EtaConfidence.LOW,
    ]


async def test_fight_lifecycle_updates_card_state():
    engine, _bus = await make_engine()
    await engine.handle_fight_event(
        "f1", fight_event(FightEventType.FIGHT_STARTED, T0 + mins(1), "f1")
    )
    assert engine.card.fight("f1").status is FightStatus.LIVE
    await engine.handle_fight_event(
        "f1", fight_event(FightEventType.FIGHT_FINISHED, T0 + mins(6), "f1")
    )
    f1 = engine.card.fight("f1")
    assert f1.status is FightStatus.FINISHED
    assert f1.duration == mins(5)


async def test_quick_finish_publishes_earlier_etas():
    engine, bus = await make_engine()
    initial_f2 = eta_updates(bus, "f2")[-1].eta_start
    await engine.handle_fight_event("f1", fight_event(FightEventType.FIGHT_STARTED, T0, "f1"))
    await engine.handle_fight_event(
        "f1", fight_event(FightEventType.FIGHT_FINISHED, T0 + mins(5), "f1")
    )
    assert eta_updates(bus, "f2")[-1].eta_start < initial_f2


async def test_noise_gate_suppresses_tiny_shifts_but_next_fight_always_published():
    engine, bus = await make_engine()
    # CARD_UPDATED ничего не меняет: пересчёт даёт те же ETA (сдвиг 0 < 2 мин).
    await engine.handle_fight_event(None, fight_event(FightEventType.CARD_UPDATED, T0))
    assert len(eta_updates(bus, "f3")) == 1  # дальний бой не переопубликован
    assert len(eta_updates(bus, "f1")) == 2  # следующий бой публикуется всегда


async def test_cancelled_fight_shifts_later_fights_earlier():
    engine, bus = await make_engine()
    f3_before = eta_updates(bus, "f3")[-1].eta_start
    await engine.handle_fight_event(
        "f2", fight_event(FightEventType.FIGHT_CANCELLED, T0 + mins(1), "f2")
    )
    assert engine.card.fight("f2").status is FightStatus.CANCELLED
    assert eta_updates(bus, "f3")[-1].eta_start < f3_before
