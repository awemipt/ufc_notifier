"""Симулятор: корректная последовательность, виртуальное время, публикация в шину."""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from event_tracker.adapters.simulator import SimulatorAdapter
from event_tracker.tracker import run_tracker
from ufc_common.bus import InMemoryBus
from ufc_common.events import TOPIC_FIGHT_EVENTS, FightEventType

SCENARIO = Path(__file__).parents[3] / "simulator-data" / "ufc_fight_night_sample.json"


async def collect(adapter: SimulatorAdapter):
    return [ev async for ev in adapter.stream()]


async def test_full_card_yields_started_and_finished_per_fight():
    events = await collect(SimulatorAdapter(SCENARIO, speedup=0))
    assert len(events) == 1 + 13 * 2  # EVENT_STARTED + (STARTED+FINISHED) × 13
    assert events[0].type is FightEventType.EVENT_STARTED
    started = [e for e in events if e.type is FightEventType.FIGHT_STARTED]
    finished = [e for e in events if e.type is FightEventType.FIGHT_FINISHED]
    assert [e.fight_id for e in started] == [f"f{i:02d}" for i in range(1, 14)]
    assert [e.fight_id for e in finished] == [f"f{i:02d}" for i in range(1, 14)]


async def test_virtual_time_is_monotonic_and_matches_scenario():
    events = await collect(SimulatorAdapter(SCENARIO, speedup=0))
    times = [e.occurred_at for e in events]
    assert times == sorted(times)
    t0 = datetime(2026, 8, 29, 22, 0, tzinfo=UTC)
    assert events[0].occurred_at == t0
    assert events[1].occurred_at == t0 + timedelta(minutes=2)  # first_fight_delay_min
    # Длительность первого боя = sim_duration_min из сценария.
    assert events[2].occurred_at - events[1].occurred_at == timedelta(minutes=16.5)


async def test_cancelled_fight_emits_cancellation_without_consuming_time(tmp_path):
    scenario = json.loads(SCENARIO.read_text())
    scenario["fights"] = scenario["fights"][:3]
    scenario["fights"][1]["cancelled"] = True
    path = tmp_path / "scenario.json"
    path.write_text(json.dumps(scenario))

    events = await collect(SimulatorAdapter(path, speedup=0))
    cancelled = [e for e in events if e.type is FightEventType.FIGHT_CANCELLED]
    assert [e.fight_id for e in cancelled] == ["f02"]
    # Два оставшихся боя отыграны полностью.
    assert sum(e.type is FightEventType.FIGHT_FINISHED for e in events) == 2


async def test_tracker_publishes_every_event_to_the_bus():
    bus = InMemoryBus()
    count = await run_tracker(SimulatorAdapter(SCENARIO, speedup=0), bus)
    assert count == 27
    assert len(bus.published) == 27
    assert all(topic == TOPIC_FIGHT_EVENTS for topic, _k, _e in bus.published)
