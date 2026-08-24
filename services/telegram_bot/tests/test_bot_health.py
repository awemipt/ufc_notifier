from httpx import ASGITransport, AsyncClient
from telegram_bot.main import create_app


async def test_health():
    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        assert (await client.get("/healthz")).status_code == 200
