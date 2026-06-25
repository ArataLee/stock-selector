from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from src.shared.domain.StockCode import StockCode


@dataclass
class UserPreferences:
    default_dimensions: list[str] = field(default_factory=lambda: ["financial", "industry", "valuation"])
    default_universe: str = "all"
    batch_size: int = 20


@dataclass
class WatchlistItem:
    code: StockCode
    added_at: str


class UserRepository(ABC):
    @abstractmethod
    async def get_preferences(self) -> UserPreferences:
        ...

    @abstractmethod
    async def save_preferences(self, prefs: UserPreferences) -> None:
        ...

    @abstractmethod
    async def get_watchlist(self) -> list[WatchlistItem]:
        ...

    @abstractmethod
    async def add_to_watchlist(self, code: StockCode) -> None:
        ...

    @abstractmethod
    async def remove_from_watchlist(self, code: StockCode) -> None:
        ...
