from __future__ import annotations
import re
from src.shared.domain.Market import Market

_SH_PREFIXES = {"6", "688"}
_SZ_PREFIXES = {"0", "2", "3"}  # 300创业板，002中小板，000主板
_BJ_PREFIXES = {"8", "4"}

_CODE_PATTERN = re.compile(r"^(\d{6})\.(SH|SZ|BJ)$")


class StockCode:
    def __init__(self, raw: str) -> None:
        m = _CODE_PATTERN.match(raw.upper())
        if not m:
            raise ValueError(f"Invalid stock code format: {raw}. Expected format: 600001.SH")
        self._digits = m.group(1)
        self._market = Market(m.group(2))
        self._raw = f"{self._digits}.{self._market.value}"

    @property
    def raw(self) -> str:
        return self._raw

    @property
    def digits(self) -> str:
        return self._digits

    @property
    def market(self) -> Market:
        return self._market

    @staticmethod
    def from_digits(digits: str) -> StockCode:
        if len(digits) != 6 or not digits.isdigit():
            raise ValueError("Stock code digits must be 6 characters")
        prefix = digits[:1]
        if digits.startswith("688") or prefix in _SH_PREFIXES:
            if prefix in _SH_PREFIXES:
                return StockCode(f"{digits}.SH")
        if digits.startswith("300") or prefix in _SZ_PREFIXES:
            if prefix in _SZ_PREFIXES:
                return StockCode(f"{digits}.SZ")
        if prefix in _BJ_PREFIXES:
            return StockCode(f"{digits}.BJ")
        return StockCode(f"{digits}.SH")  # fallback

    def __str__(self) -> str:
        return self._raw

    def __repr__(self) -> str:
        return f"StockCode({self._raw!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, StockCode):
            return NotImplemented
        return self._raw == other._raw

    def __hash__(self) -> int:
        return hash(self._raw)
