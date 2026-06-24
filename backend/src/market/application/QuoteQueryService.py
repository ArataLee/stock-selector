# src/market/application/QuoteQueryService.py
from src.shared.domain.StockCode import StockCode
from src.market.domain.MarketData import Quote, QuoteRepository


class QuoteQueryService:
    def __init__(self, quote_repo: QuoteRepository) -> None:
        self._repo = quote_repo

    async def get_quote(self, code_str: str) -> Quote | None:
        code = StockCode(code_str)
        return await self._repo.fetch_one(code)

    async def get_quotes(self, code_strs: list[str]) -> list[Quote]:
        codes = [StockCode(s) for s in code_strs]
        return await self._repo.fetch_batch(codes)
