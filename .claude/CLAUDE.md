# UFC Fight Notifier — правила работы

## Разделение труда (ГЛАВНОЕ ПРАВИЛО)

Это учебный DevOps-проект. Пользователь — DevOps-инженер, прокачивающий стек:
Kubernetes/OpenShift, Jenkins (Groovy), ArgoCD, Ansible, Helm, Istio,
Prometheus/Grafana, Zabbix, Kafka, Nginx/HAProxy, PostgreSQL, Nexus, Linux/bash, IaC.

- Claude ПИШЕТ: код приложений на Python (`services/`, `libs/`), тесты, миграции
  Alembic, бизнес-логику, `docs/`, задания в `devops-tasks/`, dev-скрипты в `scripts/`.
- Claude НЕ ПИШЕТ (даже если «быстрее самому»): Dockerfile, docker-compose,
  k8s-манифесты, Helm-чарты, Jenkinsfile, конфиги ArgoCD/Istio/Nginx/Ansible/
  Prometheus/Zabbix — всё внутри `deploy/`. Вместо этого Claude создаёт или
  обновляет задание в `devops-tasks/` по шаблону (`devops-tasks/_template.md`).
- Каталог `deploy/` принадлежит пользователю. Claude может ЧИТАТЬ его для ревью,
  указывать на ошибки и давать подсказки (сначала наводящие; прямой ответ — только
  если пользователь явно просит), но не редактирует файлы там без явной просьбы
  «напиши за меня».
- Если для работы приложения нужен новый инфраструктурный элемент — Claude сначала
  пишет задание, а код делает деградирующим мягко (feature flag / заглушка / InMemory
  реализация), пока пользователь не выполнит задание.

## Технические соглашения

- Python 3.12, FastAPI, SQLAlchemy 2 (async), aiogram 3 (Phase 1+), aiokafka (Phase 1+),
  pytest, ruff. Окружение: `.venv` в корне, `make install`.
- Схемы событий — только через `libs/ufc_common/ufc_common/events.py` (Pydantic),
  контракты топиков описаны в `docs/events.md`. Менять контракт = новая versioned-схема
  (`*.v2`), старую не ломать.
- Обмен между сервисами — только через шину (`ufc_common.bus.EventBus`) и REST API.
  Чужие схемы БД не трогать: `schedule` / `subscriptions` / `notifications`.
- Все сервисы: `/healthz`, `/readyz`, позже `/metrics`; JSON-логи (structlog);
  конфиг только из env (`ufc_common.settings`).
- Тесты обязательны для новой бизнес-логики; интеграционные — testcontainers (Phase 1+).
- Пакет каждого сервиса называется по имени сервиса (`schedule_engine`, а не `app`) —
  иначе editable-установки в монорепо конфликтуют.

## Процесс

- Статус заданий — `devops-tasks/PROGRESS.md`; при сдаче модуля Claude проходит
  по критериям приёмки из задания и пишет ревью.
- Коммиты и push — только по явной просьбе пользователя.
- `make test` / `make lint` / `make demo` должны быть зелёными перед сдачей любой работы.
