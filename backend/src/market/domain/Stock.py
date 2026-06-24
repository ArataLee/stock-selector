from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from src.shared.domain.StockCode import StockCode
from src.shared.domain.Market import Market


@dataclass(frozen=True)
class Stock:
    code: StockCode
    name: str
    listing_date: date | None = None


class StockRepository(ABC):
    @abstractmethod
    async def find(self, code: StockCode) -> Stock | None:
        ...

    @abstractmethod
    async def search(self, keyword: str) -> list[Stock]:
        ...
