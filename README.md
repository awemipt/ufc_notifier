# UFC Fight Notifier

Сервис уведомлений о боях UFC. У ивента известен порядок боёв, но не время их начала
(~30 минут между боями). Сервис отслеживает окончание боёв, пересчитывает ETA
следующих и уведомляет подписчиков заранее (Telegram, позже — робозвонок/SMS/email).

Проект одновременно является **учебным DevOps-полигоном**: приложение пишет Claude,
всю инфраструктуру (`deploy/`) делает владелец проекта по заданиям из `devops-tasks/`.
Правила зафиксированы в [.claude/CLAUDE.md](.claude/CLAUDE.md).

## Архитектура

Пять Python-сервисов + gateway, событийная шина (Phase 0 — in-memory, Phase 1 — Kafka):

| Сервис | Роль |
|---|---|
| `event_tracker` | Ингест фактов о боях через pluggable-адаптеры (симулятор → ESPN/новости) |
| `schedule_engine` | Пересчёт ETA боёв по факту окончания предыдущих |
| `subscription_service` | Пользователи, подписки, JWT-auth, REST API |
| `notification_service` | Планирование и доставка уведомлений (retry, DLQ, каналы) |
| `telegram_bot` | UI: просмотр карда, подписка на бои |
| api-gateway | Nginx → Istio (полностью в `deploy/`, зона владельца) |

Подробнее: [docs/architecture.md](docs/architecture.md), контракты событий — [docs/events.md](docs/events.md).

## Быстрый старт (Phase 0, без Docker)

```bash
make install   # создаёт .venv и ставит все пакеты (editable)
make test      # юнит-тесты всех сервисов
make lint      # ruff
make demo      # in-process прогон: симулятор → ETA → уведомления в консоль
```

## Структура

```
services/            # микросервисы (код — Claude)
libs/ufc_common/     # общая библиотека: схемы событий, шина, health, логи
deploy/              # ВСЯ инфраструктура — зона владельца проекта
devops-tasks/        # задания по DevOps-треку (00–12) + PROGRESS.md
docs/                # архитектура, контракты, ADR
simulator-data/      # сценарии кардов для симулятора
scripts/             # dev-хелперы
```

## Роадмап

- **Phase 0** — скелет, ETA-алгоритм, симулятор, in-process демо ✅ (текущая)
- **Phase 1** — MVP на docker-compose: Kafka, Postgres, Nginx, реальный Telegram-бот
- **Phase 2** — Jenkins, Nexus, k8s (k3s), Helm, ArgoCD
- **Phase 3** — Prometheus/Grafana, Zabbix, Istio (mTLS, canary)
- **Phase 4** — реальные источники данных, робозвонок/email, billing, VPS
