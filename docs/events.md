# Контракты событий (Kafka-топики)

Все payload — JSON, Pydantic-схемы в `libs/ufc_common/ufc_common/events.py`.
Каждое событие несёт `schema_version`. Изменение контракта = новый топик `*.v2`.

| Топик | Key | Producer → Consumer | Схема |
|---|---|---|---|
| `fight-events.v1` | `fight_id` (или `event_id`) | event_tracker → schedule_engine | `FightEvent` |
| `fight-eta.v1` (compacted) | `fight_id` | schedule_engine → notification_service, telegram_bot | `EtaUpdate` |
| `subscription-events.v1` | `subscription_id` | subscription_service → notification_service | `SubscriptionEvent` |
| `notification-requests.v1` | `subscription_id` | notification_service (scheduler → delivery) | `NotificationRequest` |
| `notification-requests.dlq.v1` | `subscription_id` | delivery → ops/алерты | `NotificationRequest` + ошибка |

## FightEvent (`fight-events.v1`)

Типы: `EVENT_STARTED`, `FIGHT_STARTED`, `FIGHT_FINISHED`, `FIGHT_CANCELLED`, `CARD_UPDATED`.

```json
{
  "schema_version": 1,
  "type": "FIGHT_FINISHED",
  "event_id": "ufc-fn-2026-08-29",
  "fight_id": "f03",
  "occurred_at": "2026-08-29T23:14:02Z",
  "payload": {"method": "KO", "round": 1}
}
```

## EtaUpdate (`fight-eta.v1`)

Compacted-топик: последнее сообщение по ключу = актуальный ETA боя.

```json
{
  "schema_version": 1,
  "event_id": "ufc-fn-2026-08-29",
  "fight_id": "f07",
  "eta_start": "2026-08-29T23:41:00Z",
  "confidence": "medium",
  "computed_at": "2026-08-29T23:14:02Z"
}
```

`confidence`: `high` — следующий бой, `medium` — через 1–2 боя, `low` — дальше.

## SubscriptionEvent (`subscription-events.v1`)

Типы: `CREATED`, `CANCELLED`. Несёт всё нужное notification_service для
материализованной вьюхи (без обратных синхронных вызовов): `subscription_id`,
`user_id`, `fight_id`, `lead_time_min`, `channel`, `telegram_chat_id`.

## NotificationRequest (`notification-requests.v1`)

Внутренний топик notification_service: отделяет «пора отправлять» от «отправь»,
даёт ретраи. `subscription_id`, `user_id`, `fight_id`, `channel`, `eta_start`,
`fire_at`, `message`.
