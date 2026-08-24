from datetime import UTC, datetime

from ufc_common.events import (
    EtaConfidence,
    EtaUpdate,
    FightEvent,
    FightEventType,
)

NOW = datetime(2026, 8, 29, 22, 0, tzinfo=UTC)


def test_fight_event_roundtrip():
    ev = FightEvent(
        type=FightEventType.FIGHT_FINISHED,
        event_id="ev1",
        fight_id="f03",
        occurred_at=NOW,
        payload={"method": "KO", "round": 1},
    )
    restored = FightEvent.model_validate_json(ev.model_dump_json())
    assert restored == ev
    assert restored.schema_version == 1
    assert restored.key == "f03"


def test_fight_event_key_falls_back_to_event_id():
    ev = FightEvent(type=FightEventType.EVENT_STARTED, event_id="ev1", occurred_at=NOW)
    assert ev.key == "ev1"


def test_eta_update_serializes_confidence_as_string():
    upd = EtaUpdate(
        event_id="ev1",
        fight_id="f07",
        eta_start=NOW,
        confidence=EtaConfidence.MEDIUM,
        computed_at=NOW,
        occurred_at=NOW,
    )
    assert '"confidence":"medium"' in upd.model_dump_json()
