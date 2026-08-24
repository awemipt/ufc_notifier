"""API-тесты: auth, CRUD подписок, публикация событий в шину, кард."""

from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from subscription_service.main import create_app
from subscription_service.settings import Settings
from ufc_common.bus import InMemoryBus
from ufc_common.events import TOPIC_SUBSCRIPTION_EVENTS, SubscriptionEventType

SCENARIO = Path(__file__).parents[3] / "simulator-data" / "ufc_fight_night_sample.json"


@pytest.fixture
def bus() -> InMemoryBus:
    return InMemoryBus()


@pytest.fixture
async def client(bus):
    settings = Settings(
        database_url="sqlite+aiosqlite:///:memory:",
        jwt_secret="test-secret-with-enough-entropy-0123456789",
        card_file=str(SCENARIO),
    )
    app = create_app(settings, bus)
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            yield c


async def auth(client: AsyncClient, telegram_id: int = 111) -> dict[str, str]:
    resp = await client.post(
        "/auth/telegram", json={"telegram_id": telegram_id, "username": "alice"}
    )
    assert resp.status_code == 200
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


async def test_auth_is_idempotent_per_telegram_id(client):
    first = await client.post("/auth/telegram", json={"telegram_id": 42})
    second = await client.post("/auth/telegram", json={"telegram_id": 42})
    assert first.json()["user_id"] == second.json()["user_id"]


async def test_subscriptions_require_token(client):
    assert (await client.get("/subscriptions")).status_code == 401
    resp = await client.get(
        "/subscriptions", headers={"Authorization": "Bearer not-a-jwt"}
    )
    assert resp.status_code == 401


async def test_subscribe_and_list(client, bus):
    headers = await auth(client)
    resp = await client.post(
        "/subscriptions", json={"fight_id": "f05", "lead_time_min": 10}, headers=headers
    )
    assert resp.status_code == 201
    subs = (await client.get("/subscriptions", headers=headers)).json()
    assert [s["fight_id"] for s in subs] == ["f05"]

    published = [e for t, _k, e in bus.published if t == TOPIC_SUBSCRIPTION_EVENTS]
    assert len(published) == 1
    assert published[0].type is SubscriptionEventType.CREATED
    assert published[0].fight_id == "f05"
    assert published[0].telegram_chat_id == 111


async def test_duplicate_subscription_conflicts(client):
    headers = await auth(client)
    body = {"fight_id": "f05"}
    assert (await client.post("/subscriptions", json=body, headers=headers)).status_code == 201
    assert (await client.post("/subscriptions", json=body, headers=headers)).status_code == 409


async def test_cancel_subscription_publishes_event_and_hides_it(client, bus):
    headers = await auth(client)
    sub = (
        await client.post("/subscriptions", json={"fight_id": "f09"}, headers=headers)
    ).json()
    resp = await client.delete(f"/subscriptions/{sub['id']}", headers=headers)
    assert resp.status_code == 204
    assert (await client.get("/subscriptions", headers=headers)).json() == []
    types = [e.type for t, _k, e in bus.published if t == TOPIC_SUBSCRIPTION_EVENTS]
    assert types == [SubscriptionEventType.CREATED, SubscriptionEventType.CANCELLED]


async def test_cannot_cancel_foreign_subscription(client):
    alice = await auth(client, telegram_id=1)
    bob = await auth(client, telegram_id=2)
    sub = (
        await client.post("/subscriptions", json={"fight_id": "f01"}, headers=alice)
    ).json()
    assert (await client.delete(f"/subscriptions/{sub['id']}", headers=bob)).status_code == 404


async def test_fights_endpoint_serves_the_card(client):
    resp = await client.get("/fights")
    assert resp.status_code == 200
    card = resp.json()
    assert card["event_id"] == "ufc-fn-2026-08-29"
    assert len(card["fights"]) == 13
    assert card["fights"][-1]["scheduled_rounds"] == 5


async def test_health_endpoints(client):
    assert (await client.get("/healthz")).status_code == 200
    assert (await client.get("/readyz")).status_code == 200
