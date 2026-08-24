# 02. docker-compose: Kafka, Postgres, Nginx + сервисы

## Цель
Поднимать многосервисный стек одной командой: healthchecks, порядок старта,
сети, тома, конфигурация через env. Первое знакомство с Kafka и reverse-proxy.

## Контекст
Образы из модуля 01 готовы. Теперь — целый стек: инфраструктура (Kafka, Postgres,
Nginx) + 5 сервисов. Важно: `KafkaBus` в коде ещё заглушка — Claude реализует его
(Phase 1) СРАЗУ ПОСЛЕ сдачи этого модуля, когда будет живой брокер. Поэтому
сквозной сценарий здесь — инфраструктурный: стек здоров, топики создаются,
subscription_service работает через Nginx с Postgres. Полный e2e (симулятор →
Telegram) станет приёмкой Phase 1.

## Артефакты
1. `deploy/compose/docker-compose.yml`:
   - **kafka** — Apache Kafka в KRaft-режиме (без Zookeeper), healthcheck через
     `kafka-topics.sh --list`;
   - **postgres** — postgres:16, том для данных, healthcheck `pg_isready`,
     init-скрипт `deploy/compose/initdb/01-schemas.sql`, создающий схемы
     `schedule`, `subscriptions`, `notifications`;
   - **nginx** — конфиг `deploy/nginx/nginx.conf`: `/api/*` → subscription_service:8000
     (со срезанием префикса), `/tg/webhook` → telegram_bot:8000; порт 8080 наружу;
   - 5 сервисов из образов модуля 01; env: `DATABASE_URL`,
     `KAFKA_BOOTSTRAP_SERVERS=kafka:9092`; `depends_on` с `condition: service_healthy`;
   - именованные тома, отдельная сеть, `restart: unless-stopped`.
2. `deploy/compose/.env.example` — все переменные с комментариями.
3. Упражнение со звёздочкой: вариант `docker-compose.zookeeper.yml` с Kafka+Zookeeper
   (старая схема, встречается в проде повсеместно) — поднять, посмотреть, понять
   отличия KRaft, погасить.

## Критерии приёмки
- [ ] `docker compose -f deploy/compose/docker-compose.yml up -d` → `docker compose ps`:
      все контейнеры `healthy`/`running`, ни одного в рестарт-цикле.
- [ ] `curl localhost:8080/api/healthz` → 200 через Nginx.
- [ ] Полный REST-флоу через gateway:
      `POST /api/auth/telegram` → токен → `POST /api/subscriptions` (201) →
      `GET /api/subscriptions` показывает подписку → данные лежат в Postgres
      (`docker compose exec postgres psql -U ufc -c 'select * from subscriptions'`).
- [ ] Kafka жива: создай топик `fight-events.v1` из CLI внутри контейнера,
      `kafka-console-producer`/`consumer` гоняют сообщение туда-обратно.
- [ ] `docker compose down && up -d` → данные Postgres пережили рестарт (том).
- [ ] Останови postgres: `/api/readyz` subscription_service должен отражать проблему
      (если нет — это баг приложения, заведи его Claude как задачу, не чини сам).

## Что почитать
- Compose file reference: https://docs.docker.com/compose/compose-file/
- Kafka KRaft quick start (Docker): https://kafka.apache.org/quickstart
- Nginx reverse proxy: https://docs.nginx.com/nginx/admin-guide/web-server/reverse-proxy/

## Как сдать
1. Отметь статус в `devops-tasks/PROGRESS.md`.
2. Скажи Claude: «прими модуль 02». После приёмки Claude реализует `KafkaBus`,
   consumer-циклы и настоящий Telegram-канал — и вы вместе прогоните первый
   полный e2e-сценарий.
