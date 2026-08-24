"""Симулятор ивента: проигрывает сценарий из simulator-data/ с виртуальным временем.

speedup > 0 — реальные паузы, сжатые в speedup раз (SIM_SPEEDUP=60 → вечер за ~5 мин).
speedup = 0 — мгновенный прогон (тесты и `make demo`); время событий остаётся виртуальным.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from ufc_common.events import FightEvent, FightEventType

from .base import SourceAdapter


class SimulatorAdapter(SourceAdapter):
    def __init__(self, scenario_path: str | Path, speedup: float = 60.0) -> None:
        self._scenario: dict[str, Any] = json.loads(Path(scenario_path).read_text())
        self._speedup = speedup

    @property
    def scenario(self) -> dict[str, Any]:
        return self._scenario

    async def stream(self) -> AsyncIterator[FightEvent]:
        event = self._scenario["event"]
        sim = self._scenario.get("sim", {})
        turnaround = timedelta(minutes=sim.get("turnaround_min", 12.0))
        first_delay = timedelta(minutes=sim.get("first_fight_delay_min", 0.0))

        event_id = event["id"]
        now = datetime.fromisoformat(event["scheduled_start"])
        yield FightEvent(type=FightEventType.EVENT_STARTED, event_id=event_id, occurred_at=now)

        first = True
        for fight in sorted(self._scenario["fights"], key=lambda f: f["order_no"]):
            fight_id = fight["id"]
            if fight.get("cancelled"):
                yield FightEvent(
                    type=FightEventType.FIGHT_CANCELLED,
                    event_id=event_id,
                    fight_id=fight_id,
                    occurred_at=now,
                    payload={"reason": fight.get("cancel_reason", "unknown")},
                )
                continue

            gap = first_delay if first else turnaround
            first = False
            now = await self._advance(now, gap)
            yield FightEvent(
                type=FightEventType.FIGHT_STARTED,
                event_id=event_id,
                fight_id=fight_id,
                occurred_at=now,
            )

            duration = timedelta(minutes=fight["sim_duration_min"])
            now = await self._advance(now, duration)
            yield FightEvent(
                type=FightEventType.FIGHT_FINISHED,
                event_id=event_id,
                fight_id=fight_id,
                occurred_at=now,
                payload={
                    "method": fight.get("sim_method", "decision"),
                    "duration_min": fight["sim_duration_min"],
                },
            )

    async def _advance(self, now: datetime, delta: timedelta) -> datetime:
        if self._speedup > 0:
            await asyncio.sleep(delta.total_seconds() / self._speedup)
        return now + delta
