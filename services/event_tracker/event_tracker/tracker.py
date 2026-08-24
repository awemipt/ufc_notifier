"""Прогон адаптера: каждое событие источника уходит в шину (fight-events.v1)."""

from __future__ import annotations

from ufc_common.bus import EventBus
from ufc_common.events import TOPIC_FIGHT_EVENTS
from ufc_common.logging import get_logger

from .adapters.base import SourceAdapter

log = get_logger(__name__)


async def run_tracker(adapter: SourceAdapter, bus: EventBus) -> int:
    """Возвращает число опубликованных событий (удобно в тестах и демо)."""
    count = 0
    async for event in adapter.stream():
        await bus.publish(TOPIC_FIGHT_EVENTS, event.key, event)
        count += 1
        log.debug("fight event published", type=event.type, fight_id=event.fight_id)
    return count
