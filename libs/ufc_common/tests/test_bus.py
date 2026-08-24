from datetime import UTC, datetime

import pytest
from ufc_common.bus import InMemoryBus, KafkaBus
from ufc_common.events import FightEvent, FightEventType

NOW = datetime(2026, 8, 29, 22, 0, tzinfo=UTC)


def _event(fight_id: str = "f01") -> FightEvent:
    return FightEvent(
        type=FightEventType.FIGHT_STARTED, event_id="ev1", fight_id=fight_id, occurred_at=NOW
    )


async def test_inmemory_bus_delivers_to_subscribers_in_order():
    bus = InMemoryBus()
    received: list[str] = []

    async def handler(key, event):
        received.append(key)

    bus.subscribe("t", handler)
    bus.subscribe("t", handler)
    await bus.publish("t", "k1", _event())
    assert received == ["k1", "k1"]
    assert len(bus.published) == 1


async def test_inmemory_bus_ignores_topics_without_subscribers():
    bus = InMemoryBus()
    await bus.publish("nobody-listens", None, _event())
    assert bus.published[0][0] == "nobody-listens"


def test_kafka_bus_is_a_phase1_stub():
    with pytest.raises(NotImplementedError, match="02-compose"):
        KafkaBus("localhost:9092")
