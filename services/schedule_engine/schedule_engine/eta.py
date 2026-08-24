"""ETA-алгоритм: чистые функции над кардом, без I/O. Описание — docs/architecture.md.

Идея: якорь (конец последнего боя) + сумма (turnaround + ожидаемая длительность)
по всем боям до целевого. Ожидаемая длительность = приор по числу раундов,
умноженный на EWMA отношения факт/приор уже завершённых боёв вечера.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from .models import Card, Fight, FightStatus


@dataclass(frozen=True)
class EtaConfig:
    turnaround_min: float = 12.0
    # У main event выходы бойцов и церемонии дольше.
    main_event_turnaround_min: float = 18.0
    prior_duration_min: dict[int, float] = field(default_factory=lambda: {3: 9.0, 5: 14.0})
    ewma_alpha: float = 0.3
    noise_gate_min: float = 2.0


def duration_ratio(card: Card, config: EtaConfig) -> float:
    """EWMA отношения (фактическая длительность / приор) по завершённым боям, в порядке карда.

    Стартует с 1.0 (доверие приору); ночь быстрых нокаутов уводит коэффициент вниз.
    """
    ratio = 1.0
    for fight in card.fights:
        if fight.status is not FightStatus.FINISHED or fight.duration is None:
            continue
        prior = _prior_minutes(fight, config)
        sample = (fight.duration.total_seconds() / 60.0) / prior
        ratio = config.ewma_alpha * sample + (1 - config.ewma_alpha) * ratio
    return ratio


def expected_duration(fight: Fight, ratio: float, config: EtaConfig) -> timedelta:
    return timedelta(minutes=_prior_minutes(fight, config) * ratio)


def turnaround_before(fight: Fight, card: Card, config: EtaConfig) -> timedelta:
    if fight.id == card.main_event().id:
        return timedelta(minutes=config.main_event_turnaround_min)
    return timedelta(minutes=config.turnaround_min)


def compute_etas(card: Card, config: EtaConfig, now: datetime | None = None) -> dict[str, datetime]:
    """ETA начала каждого предстоящего боя. ETA не бывает в прошлом (кламп к now)."""
    ratio = duration_ratio(card, config)
    cursor, anchored_to_fight = _anchor(card, config, ratio)
    etas: dict[str, datetime] = {}
    first = True
    for fight in card.upcoming():
        # Если якорь — плановое начало ивента, первый бой стартует прямо в него.
        if anchored_to_fight or not first:
            cursor += turnaround_before(fight, card, config)
        if now is not None and cursor < now:
            cursor = now
        etas[fight.id] = cursor
        cursor += expected_duration(fight, ratio, config)
        first = False
    return etas


def _prior_minutes(fight: Fight, config: EtaConfig) -> float:
    default = config.prior_duration_min.get(3, 9.0)
    return config.prior_duration_min.get(fight.scheduled_rounds, default)


def _anchor(card: Card, config: EtaConfig, ratio: float) -> tuple[datetime, bool]:
    """Точка отсчёта: ожидаемый конец идущего боя → конец последнего завершённого →
    плановое начало ивента. Второй элемент — якорь привязан к бою (нужен turnaround)."""
    live = card.live_fight()
    if live is not None and live.actual_start is not None:
        return live.actual_start + expected_duration(live, ratio, config), True
    last = card.last_finished()
    if last is not None and last.actual_end is not None:
        return last.actual_end, True
    return card.scheduled_start, False
