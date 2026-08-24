"""Оркестрация: применяет FightEvent к карду, пересчитывает ETA, публикует EtaUpdate."""

from __future__ import annotations

from datetime import datetime

from ufc_common.bus import EventBus
from ufc_common.events import (
    TOPIC_FIGHT_ETA,
    EtaConfidence,
    EtaUpdate,
    FightEvent,
    FightEventType,
)
from ufc_common.logging import get_logger

from .eta import EtaConfig, compute_etas
from .models import Card, FightStatus

log = get_logger(__name__)


class ScheduleEngine:
    def __init__(self, bus: EventBus, card: Card, config: EtaConfig | None = None) -> None:
        self._bus = bus
        self._card = card
        self._config = config or EtaConfig()
        # ETA, реально ушедшие в шину, — noise gate сравнивает с ними, а не с card.eta_start.
        self._published: dict[str, datetime] = {}

    @property
    def card(self) -> Card:
        return self._card

    async def handle_fight_event(self, key: str | None, event: FightEvent) -> None:
        self._apply(event)
        await self._recalc_and_publish(now=event.occurred_at)

    def _apply(self, event: FightEvent) -> None:
        if event.type is FightEventType.EVENT_STARTED:
            self._card.status = "live"
            return
        if event.type is FightEventType.CARD_UPDATED or event.fight_id is None:
            return
        fight = self._card.fight(event.fight_id)
        if event.type is FightEventType.FIGHT_STARTED:
            fight.status = FightStatus.LIVE
            fight.actual_start = event.occurred_at
        elif event.type is FightEventType.FIGHT_FINISHED:
            fight.status = FightStatus.FINISHED
            if fight.actual_start is None:
                fight.actual_start = event.occurred_at
            fight.actual_end = event.occurred_at
        elif event.type is FightEventType.FIGHT_CANCELLED:
            fight.status = FightStatus.CANCELLED

    async def _recalc_and_publish(self, now: datetime) -> None:
        etas = compute_etas(self._card, self._config, now=now)
        gate = self._config.noise_gate_min * 60
        for idx, fight in enumerate(self._card.upcoming()):
            new_eta = etas[fight.id]
            fight.eta_start = new_eta
            previous = self._published.get(fight.id)
            shift = abs((new_eta - previous).total_seconds()) if previous else None
            is_next = idx == 0
            if previous is not None and not is_next and shift is not None and shift <= gate:
                continue  # noise gate: мелкие сдвиги дальних боёв не спамим
            update = EtaUpdate(
                event_id=self._card.event_id,
                fight_id=fight.id,
                eta_start=new_eta,
                confidence=self._confidence(idx),
                computed_at=now,
                occurred_at=now,
            )
            self._published[fight.id] = new_eta
            await self._bus.publish(TOPIC_FIGHT_ETA, fight.id, update)

    @staticmethod
    def _confidence(position: int) -> EtaConfidence:
        if position == 0:
            return EtaConfidence.HIGH
        if position <= 2:
            return EtaConfidence.MEDIUM
        return EtaConfidence.LOW
