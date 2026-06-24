import pytest
from unittest.mock import AsyncMock, MagicMock
from src.shared.domain.StockCode import StockCode
from src.market.domain.DataSource import DataSourceId, DataSourceType
from src.market.domain.MarketData import Quote
from src.market.infrastructure.DataSourceRouter import QuoteRouter


class TestQuoteRouter:
    @pytest.fixture
    def adapter_a(self):
        adapter = MagicMock()
        adapter.fetch_one = AsyncMock()
        adapter.fetch_batch = AsyncMock()
        return adapter

    @pytest.fixture
    def adapter_b(self):
        adapter = MagicMock()
        adapter.fetch_one = AsyncMock()
        adapter.fetch_batch = AsyncMock()
        return adapter

    @pytest.mark.asyncio
    async def test_first_adapter_succeeds(self, adapter_a, adapter_b):
        code = StockCode("600001.SH")
        quote = Quote(code=code, name="测试", price=10.0)
        adapter_a.fetch_batch.return_value = [quote]

        router = QuoteRouter(adapters=[adapter_a, adapter_b])
        results = await router.fetch_batch([code])

        assert results == [quote]
        adapter_a.fetch_batch.assert_called_once()
        adapter_b.fetch_batch.assert_not_called()

    @pytest.mark.asyncio
    async def test_fallback_when_first_fails(self, adapter_a, adapter_b):
        code = StockCode("600001.SH")
        quote = Quote(code=code, name="测试", price=10.0)
        adapter_a.fetch_batch.return_value = []  # fails
        adapter_b.fetch_batch.return_value = [quote]

        router = QuoteRouter(adapters=[adapter_a, adapter_b])
        results = await router.fetch_batch([code])

        assert results == [quote]
        adapter_a.fetch_batch.assert_called_once()
        adapter_b.fetch_batch.assert_called_once()

    @pytest.mark.asyncio
    async def test_all_adapters_fail(self, adapter_a, adapter_b):
        code = StockCode("600001.SH")
        adapter_a.fetch_batch.return_value = []
        adapter_b.fetch_batch.return_value = []

        router = QuoteRouter(adapters=[adapter_a, adapter_b])
        results = await router.fetch_batch([code])

        assert results == []
