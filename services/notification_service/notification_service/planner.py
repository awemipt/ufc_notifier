"""Планировщик уведомлений.

Держит материализованную вьюху подписок (из subscription-events.v1) и актуальные ETA
(из fight-eta.v1). Уведомление должно уйти в `eta_start - lead_time`.

Phase 0: состояние в памяти, дедупликация — set. Phase 1: таблица deliveries
(UNIQUE(subscription, fight, channel)), ретраи, DLQ.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from ufc_common.events import (
    EtaUpdate,
    NotificationRequest,
    SubscriptionEvent,
    SubscriptionEventType,
)


class NotificationPlanner:
    def __init__(self) -> None:
        self._subscriptions: dict[str, SubscriptionEvent] = {}
        self._etas: dict[str, EtaUpdate] = {}
        self._sent: set[tuple[str, str]] = set()  # (subscription_id, fight_id)

    async def handle_subscription_event(self, key: str | None, event: SubscriptionEvent) -> None:
        if event.type is SubscriptionEventType.CREATED:
            self._subscriptions[event.subscription_id] = event
        elif event.type is SubscriptionEventType.CANCELLED:
            self._subscriptions.pop(event.subscription_id, None)

    async def handle_eta_update(self, key: str | None, event: EtaUpdate) -> None:
        self._etas[event.fight_id] = event

    def due(self, now: datetime) -> list[NotificationRequest]:
        """Уведомления, чьё время пришло. Каждое возвращается ровно один раз."""
        requests: list[NotificationRequest] = []
        for sub in self._subscriptions.values():
            eta = self._etas.get(sub.fight_id)
            if eta is None or (sub.subscription_id, sub.fight_id) in self._sent:
                continue
            fire_at = eta.eta_start - timedelta(minutes=sub.lead_time_min)
            if fire_at > now:
                continue
            self._sent.add((sub.subscription_id, sub.fight_id))
            requests.append(
                NotificationRequest(
                    subscription_id=sub.subscription_id,
                    user_id=sub.user_id,
                    fight_id=sub.fight_id,
                    channel=sub.channel,
                    eta_start=eta.eta_start,
                    fire_at=fire_at,
                    message=(
                        f"Бой скоро начнётся: ориентировочно в "
                        f"{eta.eta_start.strftime('%H:%M')} UTC "
                        f"(точность: {eta.confidence.value})"
                    ),
                    user_label=sub.user_label,
                    telegram_chat_id=sub.telegram_chat_id,
                    occurred_at=now,
                )
            )
        requests.sort(key=lambda r: r.fire_at)
        return requests
