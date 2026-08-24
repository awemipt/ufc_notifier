# Цели уровня приложения. Deploy-цели (compose, k8s и т.д.) добавляет владелец проекта.

VENV := .venv
PY := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

PACKAGES := libs/ufc_common \
            services/schedule_engine \
            services/event_tracker \
            services/subscription_service \
            services/notification_service \
            services/telegram_bot

.PHONY: venv install test lint fmt demo clean

venv:
	python3 -m venv $(VENV)
	$(PIP) install -U pip

install: venv
	$(PIP) install $(foreach p,$(PACKAGES),-e $(p)) pytest pytest-asyncio httpx ruff

test:
	$(PY) -m pytest -q

lint:
	$(VENV)/bin/ruff check .

fmt:
	$(VENV)/bin/ruff check --fix .

demo:
	$(PY) scripts/dev_run_pipeline.py

clean:
	rm -rf $(VENV) .pytest_cache .ruff_cache
	find . -type d -name __pycache__ -not -path './.venv/*' -exec rm -rf {} +
