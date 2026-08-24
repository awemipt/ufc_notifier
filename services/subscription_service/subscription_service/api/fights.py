"""Просмотр карда.

Phase 0: читаем сценарий симулятора с диска.
TODO(Phase 1): proxy к REST API schedule_engine (живые ETA и статусы боёв).
"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request

from ..schemas import CardOut, FightOut

router = APIRouter(prefix="/fights", tags=["fights"])


@router.get("", response_model=CardOut)
async def get_card(request: Request) -> CardOut:
    card_file = Path(request.app.state.settings.card_file)
    if not card_file.exists():
        raise HTTPException(status_code=503, detail=f"Card source not available: {card_file}")
    data = json.loads(card_file.read_text())
    event = data["event"]
    return CardOut(
        event_id=event["id"],
        name=event["name"],
        scheduled_start=event["scheduled_start"],
        fights=[
            FightOut(
                id=f["id"],
                order_no=f["order_no"],
                segment=f["segment"],
                fighter_red=f["fighter_red"],
                fighter_blue=f["fighter_blue"],
                scheduled_rounds=f.get("scheduled_rounds", 3),
            )
            for f in data["fights"]
        ],
    )
