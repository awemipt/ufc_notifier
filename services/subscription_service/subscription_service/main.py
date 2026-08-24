from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from ufc_common.bus import EventBus, InMemoryBus
from ufc_common.health import health_router
from ufc_common.logging import configure_logging

from .api import auth, fights, subscriptions
from .db import Base, build_engine
from .settings import Settings


def create_app(settings: Settings | None = None, bus: EventBus | None = None) -> FastAPI:
    settings = settings or Settings()
    engine, sessionmaker = build_engine(settings.database_url)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Dev-удобство; канонические миграции — alembic (см. alembic/).
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        yield
        await engine.dispose()

    app = FastAPI(title="UFC Notifier — subscription service", lifespan=lifespan)
    app.state.settings = settings
    app.state.bus = bus or InMemoryBus()
    app.state.sessionmaker = sessionmaker
    app.include_router(health_router())
    app.include_router(auth.router)
    app.include_router(fights.router)
    app.include_router(subscriptions.router)
    return app


def main() -> None:
    import uvicorn

    settings = Settings()
    configure_logging(settings.service_name, settings.log_level, settings.log_json)
    uvicorn.run(create_app(settings), host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
