import pytest
from httpx import AsyncClient, ASGITransport


@pytest.fixture
def app():
    from src.api.main import app
    return app


@pytest.mark.asyncio
async def test_list_channels_empty(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/notification/channels")
        assert resp.status_code == 200
        assert resp.json() == {"channels": []}


@pytest.mark.asyncio
async def test_list_monitors_empty(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/notification/tasks")
        assert resp.status_code == 200
        assert resp.json() == {"tasks": []}


@pytest.mark.asyncio
async def test_create_channel_invalid_type(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/notification/channels", json={
            "type": "invalid",
            "webhook_url": "https://example.com",
        })
        assert resp.status_code == 400


@pytest.mark.asyncio
async def test_create_channel_valid(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/notification/channels", json={
            "name": "test",
            "type": "wecom",
            "webhook_url": "https://qyapi.weixin.qq.com/test",
        })
        assert resp.status_code == 200
        assert resp.json()["status"] == "created"


@pytest.mark.asyncio
async def test_create_monitor(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/notification/tasks", json={
            "name": "daily scan",
            "cron_expr": "0 18 * * 1-5",
            "universe_type": "all",
        })
        assert resp.status_code == 200
