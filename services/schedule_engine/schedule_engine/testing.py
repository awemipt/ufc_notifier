"""Тестовые фабрики карда — используются в тестах schedule_engine и демо-скриптах."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from ufc_common.events import CardSegment

from .models import Card, Fight, FightStatus

T0 = datetime(2026, 8, 29, 22, 0, tzinfo=UTC)


def mins(m: float) -> timedelta:
    return timedelta(minutes=m)


def make_card() -> Card:
    fights = [
        Fight("f1", "ev1", 1, CardSegment.EARLY_PRELIMS, "Silva", "Costa"),
        Fight("f2", "ev1", 2, CardSegment.PRELIMS, "Ivanov", "Smith"),
        Fight("f3", "ev1", 3, CardSegment.PRELIMS, "Lee", "Park"),
        Fight("f4", "ev1", 4, CardSegment.MAIN_CARD, "Garcia", "Nunes"),
        Fight("f5", "ev1", 5, CardSegment.MAIN_CARD, "Jones", "Miocic", scheduled_rounds=5),
    ]
    return Card(event_id="ev1", name="UFC Test Night", scheduled_start=T0, fights=fights)


def finish(card: Card, fight_id: str, start: datetime, end: datetime) -> None:
    f = card.fight(fight_id)
    f.status = FightStatus.FINISHED
    f.actual_start = start
    f.actual_end = end
