from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from src.shared.domain.StockCode import StockCode


@dataclass(frozen=True)
class FinancialReport:
    code: StockCode
    period: str  # 报告期，如 "2024Q4"
    revenue_yoy: float | None = None  # 营收同比增长率（%）
    profit_yoy: float | None = None   # 归母净利润同比增长率（%）
    roe: float | None = None          # ROE（%）
    gross_margin: float | None = None # 毛利率（%）
    net_margin: float | None = None   # 净利率（%）


class FinancialRepository(ABC):
    @abstractmethod
    async def fetch(self, code: StockCode, periods: int = 4) -> list[FinancialReport]:
        ...

    @abstractmethod
    async def fetch_financials(self, codes: list[StockCode], periods: int = 4) -> dict[StockCode, list[FinancialReport]]:
        ...
