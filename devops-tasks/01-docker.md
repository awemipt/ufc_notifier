# 01. Dockerfile для всех сервисов

## Цель
Уметь собирать компактные production-образы Python-приложений: multi-stage сборка,
non-root, слои и кэш, `.dockerignore`.

## Контекст
Пять сервисов в `services/` — обычные Python-пакеты, каждый зависит от общей
библиотеки `libs/ufc_common`. Это ключевая особенность сборки: контекст должен
включать и сервис, и `libs/` — подумай, каким должен быть build context и почему
`docker build services/subscription_service` не сработает.

Точки входа:
- `subscription_service` — HTTP: `uvicorn` с `subscription_service.main:create_app` (factory);
- `notification_service`, `telegram_bot` — HTTP-скелеты, аналогично через `create_app`;
- `event_tracker`, `schedule_engine` — пока без самостоятельного main-цикла
  (появится с KafkaBus в Phase 1): образ собирается, контейнер может запускать
  `python -c "import event_tracker"` как smoke — сделай CMD осмысленно-заглушечным
  и оставь комментарий.

## Артефакты
1. `deploy/docker/<service>.Dockerfile` — по одному на каждый из 5 сервисов
   (допустим один параметризованный Dockerfile с `ARG SERVICE` — решение обоснуй
   комментарием в файле).
2. `deploy/docker/.dockerignore` (и симлинк/копия в корне, если собираешь из корня).
3. Требования к образу:
   - база `python:3.12-slim`, multi-stage (builder со сборкой wheel/зависимостей,
     runtime без пула компиляторов);
   - процесс работает от непривилегированного пользователя (не root);
   - слои: зависимости кэшируются отдельно от кода (перестройка при правке кода
     не тянет переустановку зависимостей);
   - итоговый образ < 250 MB;
   - `PYTHONDONTWRITEBYTECODE=1`, `PYTHONUNBUFFERED=1`.

## Критерии приёмки
- [ ] `docker build -f deploy/docker/subscription_service.Dockerfile -t ufc/subscription-service:dev .`
      (из корня) собирается для всех 5 сервисов.
- [ ] `docker run --rm -p 8000:8000 ufc/subscription-service:dev` →
      `curl localhost:8000/healthz` возвращает `{"status":"ok"}`.
- [ ] `docker image ls` — каждый образ < 250 MB.
- [ ] `docker run --rm ufc/subscription-service:dev id -u` → не `0`.
- [ ] Поменяй строку в `subscription_service/main.py` и пересобери: слой
      с pip install берётся из кэша (видно в выводе сборки).
- [ ] `.dockerignore` исключает `.venv`, `.git`, `__pycache__`, `deploy/`, тесты.

## Что почитать
- Multi-stage builds: https://docs.docker.com/build/building/multi-stage/
- Best practices: https://docs.docker.com/develop/develop-images/dockerfile_best-practices/
- Про non-root и USER: https://docs.docker.com/engine/reference/builder/#user

## Как сдать
1. Отметь статус в `devops-tasks/PROGRESS.md`.
2. Скажи Claude: «прими модуль 01» — он проверит критерии, соберёт образ и
   позадаёт вопросы «почему так» (будь готов объяснить каждый слой).
