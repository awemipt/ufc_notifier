"""Доменная модель карда. Phase 0 — in-memory; Phase 1 — персистентность (схема `schedule`)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Any

from ufc_common.events import CardSegment


class FightStatus(StrEnum):
    SCHEDULED = "scheduled"
    LIVE = "live"
    FINISHED = "finished"
    CANCELLED = "cancelled"


@dataclass
class Fight:
    id: str
    event_id: str
    order_no: int
    segment: CardSegment
    fighter_red: str
    fighter_blue: str
    scheduled_rounds: int = 3
    status: FightStatus = FightStatus.SCHEDULED
    actual_start: datetime | None = None
    actual_end: datetime | None = None
    eta_start: datetime | None = None

    @property
    def duration(self) -> timedelta | None:
        if self.actual_start and self.actual_end:
            return self.actual_end - self.actual_start
        return None

    @property
    def label(self) -> str:
        return f"{self.fighter_red} vs {self.fighter_blue}"


@dataclass
class Card:
    event_id: str
    name: str
    scheduled_start: datetime
    fights: list[Fight] = field(default_factory=list)
    status: str = "announced"

    def __post_init__(self) -> None:
        self.fights.sort(key=lambda f: f.order_no)

    def fight(self, fight_id: str) -> Fight:
        for f in self.fights:
            if f.id == fight_id:
                return f
        raise KeyError(f"unknown fight_id: {fight_id}")

    def upcoming(self) -> list[Fight]:
        return [f for f in self.fights if f.status is FightStatus.SCHEDULED]

    def live_fight(self) -> Fight | None:
        for f in self.fights:
            if f.status is FightStatus.LIVE:
                return f
        return None

    def last_finished(self) -> Fight | None:
        finished = [f for f in self.fights if f.status is FightStatus.FINISHED]
        return max(finished, key=lambda f: f.order_no) if finished else None

    def main_event(self) -> Fight:
        return max(self.fights, key=lambda f: f.order_no)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Card:
        """Строит кард из JSON-формата simulator-data (сим-поля игнорируются)."""
        event = data["event"]
        fights = [
            Fight(
                id=item["id"],
                event_id=event["id"],
                order_no=item["order_no"],
                segment=CardSegment(item["segment"]),
                fighter_red=item["fighter_red"],
                fighter_blue=item["fighter_blue"],
                scheduled_rounds=item.get("scheduled_rounds", 3),
            )
            for item in data["fights"]
        ]
        return cls(
            event_id=event["id"],
            name=event["name"],
            scheduled_start=datetime.fromisoformat(event["scheduled_start"]),
            fights=fights,
        )
