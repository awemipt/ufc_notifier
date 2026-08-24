# 00. Окружение: git, Docker, k3s, bash

## Цель
Рабочая машина готова ко всему треку: git-репозиторий проекта, Docker без sudo,
локальный k3s, базовые утилиты. Побочный навык — идемпотентные bash-скрипты
с проверками (то, что ждут от «уверенного администрирования Linux»).

## Контекст
Phase 0 приложения уже работает без инфраструктуры (`make demo`). Всё дальнейшее —
образы (01), compose (02), CI (03), кластер (05+) — опирается на это окружение.
k3s ставим сейчас, но пользоваться начнём только в модуле 05: пусть постоит.

## Артефакты
1. Инициализированный git-репозиторий в корне проекта + первый коммит
   (`.gitignore` уже есть). Ветка по умолчанию — `main`.
2. `deploy/scripts/check-env.sh` — bash-скрипт проверки окружения:
   - `set -euo pipefail` и аккуратная обработка отсутствующих команд
     (понятное сообщение, а не голый stacktrace);
   - проверяет и печатает версии: `git`, `python3` (≥3.12), `docker`,
     `docker compose`, `k3s`/`kubectl`, `make`, `curl`, `jq`;
   - проверяет, что docker работает без sudo (`docker info`);
   - проверяет, что нода k3s в статусе `Ready`;
   - выводит итоговую таблицу OK/FAIL и завершается кодом 0 только если всё OK.

## Критерии приёмки
- [ ] `git log --oneline` показывает первый коммит; `git status` чистый.
- [ ] `docker run --rm hello-world` работает из-под твоего пользователя (без sudo).
- [ ] `docker compose version` — v2.
- [ ] `kubectl get nodes` показывает ноду `Ready` (через k3s).
- [ ] `bash deploy/scripts/check-env.sh; echo $?` → таблица + `0`.
- [ ] Скрипт идемпотентен: второй запуск даёт тот же результат.
- [ ] Временно переименуй `jq` в PATH (или подмени PATH) — скрипт даёт FAIL
      по одной строке и ненулевой exit-код, а не падает с ошибкой bash.

## Что почитать
- k3s Quick-Start: https://docs.k3s.io/quick-start
- Docker post-install (rootless-доступ группой docker): https://docs.docker.com/engine/install/linux-postinstall/
- Bash strict mode: `set -euo pipefail` — http://redsymbol.net/articles/unofficial-bash-strict-mode/

## Как сдать
1. Отметь статус в `devops-tasks/PROGRESS.md`.
2. Скажи Claude: «прими модуль 00».
