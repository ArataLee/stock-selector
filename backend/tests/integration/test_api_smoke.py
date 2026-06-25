import pytest
from httpx import AsyncClient, ASGITransport


@pytest.fixture
def app():
    from src.api.main import app
    return app


@pytest.mark.asyncio
async def test_health(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_list_data_sources(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/config/data-sources")
        assert resp.status_code == 200
        data = resp.json()
        assert "sources" in data
        assert len(data["sources"]) >= 1


@pytest.mark.asyncio
async def test_list_providers_empty(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/config/llm-providers")
        assert resp.status_code == 200
        data = resp.json()
        assert "providers" in data


@pytest.mark.asyncio
async def test_list_prompts(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/config/prompts")
        assert resp.status_code == 200
        data = resp.json()
        assert "prompts" in data
        assert len(data["prompts"]) >= 2


@pytest.mark.asyncio
async def test_quote_not_found(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/market/stocks/000000.SZ/quote")
        assert resp.status_code == 404


@pytest.mark.asyncio
async def test_watchlist(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/user/watchlist")
        assert resp.status_code == 200
        assert "items" in resp.json()


@pytest.mark.asyncio
async def test_user_profile(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/user/profile")
        assert resp.status_code == 200
        data = resp.json()
        assert "default_dimensions" in data
