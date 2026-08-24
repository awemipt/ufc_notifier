"""Стандартные health-эндпоинты для всех сервисов: /healthz (liveness), /readyz (readiness)."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import APIRouter, Response

ReadinessCheck = Callable[[], Awaitable[bool]]


def health_router(readiness: ReadinessCheck | None = None) -> APIRouter:
    router = APIRouter()

    @router.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @router.get("/readyz")
    async def readyz(response: Response) -> dict[str, str]:
        ready = True if readiness is None else await readiness()
        if not ready:
            response.status_code = 503
            return {"status": "not ready"}
        return {"status": "ok"}

    return router
