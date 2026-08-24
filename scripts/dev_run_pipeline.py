"""In-process демо всего пайплайна без инфраструктуры (Phase 0).

Симулятор проигрывает кард на виртуальном времени; ScheduleEngine пересчитывает ETA;
NotificationPlanner решает, кому пора отправить уведомление; LogChannel доставляет.
Та же связка сервисов, что поедет в docker-compose/k8s, — но через InMemoryBus.

Запуск: make demo  (или .venv/bin/python scripts/dev_run_pipeline.py)
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from pathlib import Path

from event_tracker.adapters.simulator import SimulatorAdapter
from notification_service.channels.log import LogChannel
from notification_service.planner import NotificationPlanner
from schedule_engine.engine import ScheduleEngine
from schedule_engine.models import Card
from ufc_common.bus import InMemoryBus
from ufc_common.events import (
    TOPIC_FIGHT_ETA,
    TOPIC_FIGHT_EVENTS,
    TOPIC_SUBSCRIPTION_EVENTS,
    FightEventType,
    NotificationRequest,
    SubscriptionEvent,
    SubscriptionEventType,
)
from ufc_common.logging import configure_logging

ROOT = Path(__file__).resolve().parents[1]
SCENARIO = ROOT / "simulator-data" / "ufc_fight_night_sample.json"

SUBSCRIBERS = [
    ("Alice", "f05", 10),
    ("Bob", "f09", 15),
    ("Carol", "f13", 30),  # main event
]


def hm(dt: datetime) -> str:
    return dt.strftime("%H:%M")


async def main() -> None:
    configure_logging("demo", level="WARNING", json_output=False)

    data = json.loads(SCENARIO.read_text())
    card = Card.from_dict(data)
    labels = {f.id: f.label for f in card.fights}

    bus = InMemoryBus()
    engine = ScheduleEngine(bus, card)
    planner = NotificationPlanner()
    channel = LogChannel()

    bus.subscribe(TOPIC_FIGHT_EVENTS, engine.handle_fight_event)
    bus.subscribe(TOPIC_FIGHT_ETA, planner.handle_eta_update)
    bus.subscribe(TOPIC_SUBSCRIPTION_EVENTS, planner.handle_subscription_event)

    print(f"── {card.name} ── план {hm(card.scheduled_start)} UTC, {len(card.fights)} боёв\n")
    for i, (name, fight_id, lead) in enumerate(SUBSCRIBERS, start=1):
        await bus.publish(
            TOPIC_SUBSCRIPTION_EVENTS,
            f"s{i}",
            SubscriptionEvent(
                type=SubscriptionEventType.CREATED,
                subscription_id=f"s{i}",
                user_id=f"u{i}",
                fight_id=fight_id,
                lead_time_min=lead,
                user_label=name,
                occurred_at=card.scheduled_start,
            ),
        )
        print(f"       📝 {name} подписан(а) на {fight_id} {labels[fight_id]} (за {lead} мин)")
    print()

    actual_starts: dict[str, datetime] = {}
    delivered: list[NotificationRequest] = []

    async def flush_due(now: datetime) -> None:
        for req in planner.due(now):
            await channel.send(req)
            delivered.append(req)
            print(
                f"{hm(req.fire_at)}  🔔 {req.user_label}: {labels[req.fight_id]} — {req.message}"
            )

    adapter = SimulatorAdapter(SCENARIO, speedup=0)
    async for ev in adapter.stream():
        await flush_due(ev.occurred_at)
        await bus.publish(TOPIC_FIGHT_EVENTS, ev.key, ev)
        await flush_due(ev.occurred_at)

        t = hm(ev.occurred_at)
        if ev.type is FightEventType.EVENT_STARTED:
            print(f"{t}  ▶ ивент начался")
        elif ev.type is FightEventType.FIGHT_STARTED and ev.fight_id:
            actual_starts[ev.fight_id] = ev.occurred_at
            print(f"{t}  🥊 {ev.fight_id} {labels[ev.fight_id]} — начался")
        elif ev.type is FightEventType.FIGHT_FINISHED and ev.fight_id:
            method = ev.payload.get("method", "?")
            dur = ev.payload.get("duration_min", "?")
            print(f"{t}  ✅ {ev.fight_id} завершён ({method}, {dur} мин)")
            upcoming = card.upcoming()[:3]
            if upcoming:
                etas = " · ".join(
                    f"{f.id} ≈{hm(f.eta_start)}" for f in upcoming if f.eta_start
                )
                print(f"       ETA: {etas}")

    print(f"\n── итог: доставлено {len(delivered)} уведомлений ──")
    for req in delivered:
        actual = actual_starts.get(req.fight_id)
        if actual is None:
            continue
        error_min = abs((actual - req.eta_start).total_seconds()) / 60
        heads_up = (actual - req.fire_at).total_seconds() / 60
        print(
            f"  {req.user_label:<6} {req.fight_id}: уведомлён в {hm(req.fire_at)}, "
            f"бой начался в {hm(actual)} (за {heads_up:.0f} мин до боя, "
            f"ошибка ETA {error_min:.1f} мин)"
        )


if __name__ == "__main__":
    asyncio.run(main())
