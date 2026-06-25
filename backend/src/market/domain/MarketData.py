from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from src.shared.domain.StockCode import StockCode


@dataclass(frozen=True)
class Quote:
    code: StockCode
    name: str
    price: float
    pe_ttm: float | None = None
    pb: float | None = None
    market_cap: float | None = None  # 总市值（亿）
    volume: float | None = None
    trade_date: date | None = None


class QuoteRepository(ABC):
    @abstractmethod
    async def fetch_one(self, code: StockCode) -> Quote | None:
        ...

    @abstractmethod
    async def fetch_quotes(self, codes: list[StockCode]) -> list[Quote]:
        ...
