# Архитектура

## Общая схема

```
                         ┌────────────────┐
  источники данных ────▶ │ event_tracker  │──▶ fight-events.v1
  (симулятор / ESPN)     └────────────────┘         │
                                                    ▼
                         ┌────────────────┐
                         │ schedule_engine│──▶ fight-eta.v1 (compacted)
                         │  (ETA-алгоритм)│         │
                         └────────────────┘         ▼
 ┌──────────────┐  REST  ┌────────────────────┐  ┌──────────────────────┐
 │ telegram_bot │◀──────▶│subscription_service│─▶│ notification_service │
 │  (UI, aiogram)│        │ (users, subs, JWT) │  │ (планирование,       │
 └──────────────┘        └────────────────────┘  │  доставка, retry/DLQ)│
        ▲                  subscription-events.v1 └──────────┬───────────┘
        │                                                    │ каналы: telegram,
        └────────────── push (Bot API) ◀─────────────────────┘ позже call/sms/email
```

Gateway (Nginx → Istio) стоит перед `subscription_service` (`/api/*`) и
`telegram_bot` (`/tg/webhook`) — целиком в `deploy/`.

## Сервисы

### event_tracker
Единственная точка контакта с внешним миром по данным о боях. Источники подключаются
через `SourceAdapter` (async-итератор `FightEvent`). Phase 0 — `SimulatorAdapter`,
проигрывающий сценарий из `simulator-data/` с ускорением (`SIM_SPEEDUP`).
Публикует нормализованные события в `fight-events.v1`.

### schedule_engine
Владеет канонической моделью карда (схема БД `schedule` с Phase 1; Phase 0 — in-memory).
Консюмит `fight-events.v1`, пересчитывает ETA всех предстоящих боёв, публикует
`fight-eta.v1`.

Алгоритм (`schedule_engine/eta.py`, чистые функции):
- якорь = конец последнего завершённого боя (или ожидаемый конец идущего, или
  плановое начало ивента);
- `eta(k) = якорь + Σ (turnaround + expected_duration)` по всем боям до k;
- `turnaround` ≈ 12 мин (у main event больше — длинные выходы);
- `expected_duration` = приор по числу раундов (3R ≈ 9 мин, 5R ≈ 14 мин),
  умноженный на EWMA (α=0.3) отношения факт/приор уже завершённых боёв вечера —
  ночь быстрых нокаутов сдвигает ETA раньше;
- noise gate: публикуем сдвиг только если > 2 мин (для следующего боя — всегда);
- `confidence` (high/medium/low) деградирует с расстоянием до боя.

### subscription_service
FastAPI: `/auth/telegram` (идентификация по Telegram, выдача JWT), `/fights`
(просмотр карда), `/subscriptions` (CRUD). Схема БД `subscriptions`.
Изменения подписок публикует в `subscription-events.v1`, чтобы у
`notification_service` была локальная материализованная вьюха (без синхронных
вызовов на горячем пути).

### notification_service
Консюмит `fight-eta.v1` + `subscription-events.v1`, планирует доставку на
`eta − lead_time`, отправляет через `NotificationChannel`-адаптеры
(Phase 0 — `LogChannel`, Phase 1 — Telegram, Phase 4 — робозвонок/SMS/email).
Идемпотентность: UNIQUE(subscription, fight, channel) в схеме `notifications`;
ретраи + DLQ `notification-requests.dlq.v1`.

### telegram_bot
aiogram 3 в webhook-режиме за gateway. Владеет диалогами; сама доставка пушей —
у notification_service. Ходит в subscription_service по REST.

## Хранилища

Один PostgreSQL-инстанс (до Phase 2), схема-на-сервис: `schedule`, `subscriptions`,
`notifications`. Сервисы не читают чужие схемы — только API и шина.

## Шина

`ufc_common.bus.EventBus`: Phase 0 — `InMemoryBus` (in-process, для демо и тестов),
Phase 1 — `KafkaBus` (aiokafka), топики в [events.md](events.md). Интерфейс один,
чтобы бизнес-код не менялся при переходе.

## Решения (ADR-кратко)

- **Auth внутри subscription_service**, не отдельный сервис — выделение возможно позже.
- **Billing** — колонка `tier` + заглушка до Phase 4.
- **JSON-события с `schema_version`**, без Avro/Schema Registry — осознанное упрощение.
- **Монорепо** — один пайплайн CI на всё, проще для учебного трека.
