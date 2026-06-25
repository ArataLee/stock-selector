from src.shared.domain.StockCode import StockCode
from src.market.domain.Stock import Stock, StockRepository
from src.market.domain.MarketData import Quote, QuoteRepository
from src.market.domain.FinancialData import FinancialReport, FinancialRepository


class StockRouter(StockRepository):
    def __init__(self, adapters: list[StockRepository]) -> None:
        self._adapters = adapters

    async def find(self, code: StockCode) -> Stock | None:
        for adapter in self._adapters:
            result = await adapter.find(code)
            if result is not None:
                return result
        return None

    async def search(self, keyword: str) -> list[Stock]:
        for adapter in self._adapters:
            result = await adapter.search(keyword)
            if result:
                return result
        return []


class QuoteRouter(QuoteRepository):
    def __init__(self, adapters: list[QuoteRepository]) -> None:
        self._adapters = adapters

    async def fetch_one(self, code: StockCode) -> Quote | None:
        for adapter in self._adapters:
            result = await adapter.fetch_one(code)
            if result is not None:
                return result
        return None

    async def fetch_quotes(self, codes: list[StockCode]) -> list[Quote]:
        for adapter in self._adapters:
            result = await adapter.fetch_quotes(codes)
            if result:
                return result
        return []


class FinancialRouter(FinancialRepository):
    def __init__(self, adapters: list[FinancialRepository]) -> None:
        self._adapters = adapters

    async def fetch(self, code: StockCode, periods: int = 4) -> list[FinancialReport]:
        for adapter in self._adapters:
            result = await adapter.fetch(code, periods)
            if result:
                return result
        return []

    async def fetch_financials(self, codes: list[StockCode], periods: int = 4) -> dict[StockCode, list[FinancialReport]]:
        for adapter in self._adapters:
            result = await adapter.fetch_financials(codes, periods)
            if result:
                return result
        return {}
