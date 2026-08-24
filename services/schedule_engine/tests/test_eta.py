"""Контрольные сценарии ETA-алгоритма (см. docs/architecture.md).

Кард: 22:00 старт, 4 боя по 3R + main event 5R.
Дефолтные приоры: 3R=9 мин, 5R=14 мин; turnaround 12 мин (main event 18); EWMA α=0.3.
"""

from schedule_engine.eta import EtaConfig, compute_etas, duration_ratio
from schedule_engine.models import FightStatus
from schedule_engine.testing import T0, finish, make_card, mins


def test_initial_etas_from_event_start():
    """До первого боя первый ETA = плановое начало, дальше приор+turnaround."""
    etas = compute_etas(make_card(), EtaConfig(), now=T0)
    assert etas["f1"] == T0
    assert etas["f2"] == T0 + mins(21)   # 9 + 12
    assert etas["f3"] == T0 + mins(42)
    assert etas["f4"] == T0 + mins(63)


def test_main_event_gets_longer_turnaround():
    etas = compute_etas(make_card(), EtaConfig(), now=T0)
    # f5: после f4 (23:03) + 9 мин боя + 18 мин main-event turnaround = 23:30
    assert etas["f5"] == T0 + mins(90)


def test_quick_finish_shifts_remaining_etas_earlier():
    card = make_card()
    finish(card, "f1", T0, T0 + mins(5))  # KO за 5 мин вместо приора 9
    etas = compute_etas(card, EtaConfig(), now=T0 + mins(5))
    assert etas["f2"] == T0 + mins(17)  # 22:05 + turnaround, раньше исходных 22:21
    assert etas["f3"] < T0 + mins(42)


def test_slow_fight_shifts_remaining_etas_later():
    card = make_card()
    finish(card, "f1", T0, T0 + mins(15))  # затяжной бой: 15 мин против приора 9
    etas = compute_etas(card, EtaConfig(), now=T0 + mins(15))
    assert etas["f2"] == T0 + mins(27)  # 22:15 + 12, позже исходных 22:21


def test_live_fight_anchors_to_its_expected_end():
    card = make_card()
    f1 = card.fight("f1")
    f1.status = FightStatus.LIVE
    f1.actual_start = T0 + mins(2)
    etas = compute_etas(card, EtaConfig(), now=T0 + mins(2))
    assert "f1" not in etas  # идущий бой больше не «предстоящий»
    assert etas["f2"] == T0 + mins(2 + 9 + 12)  # старт + ожидаемая длительность + turnaround


def test_cancelled_fight_frees_its_slot():
    card = make_card()
    card.fight("f2").status = FightStatus.CANCELLED
    etas = compute_etas(card, EtaConfig(), now=T0)
    assert "f2" not in etas
    assert etas["f3"] == T0 + mins(21)  # f3 занял слот f2


def test_eta_is_never_in_the_past():
    """Ивент задерживается: в 22:10 ничего не началось — ETA первого боя клампится к now."""
    etas = compute_etas(make_card(), EtaConfig(), now=T0 + mins(10))
    assert etas["f1"] == T0 + mins(10)


def test_ewma_ratio_compounds_over_the_night():
    card = make_card()
    finish(card, "f1", T0, T0 + mins(4.5))  # ratio-сэмпл 0.5
    one_fast = duration_ratio(card, EtaConfig())
    finish(card, "f2", T0 + mins(17), T0 + mins(21.5))  # ещё один быстрый
    two_fast = duration_ratio(card, EtaConfig())
    assert one_fast == 0.85  # 0.3*0.5 + 0.7*1.0
    assert two_fast < one_fast


def test_ratio_starts_at_one_with_no_finished_fights():
    assert duration_ratio(make_card(), EtaConfig()) == 1.0
