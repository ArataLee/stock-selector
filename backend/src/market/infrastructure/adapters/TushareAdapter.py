# src/market/infrastructure/adapters/TushareAdapter.py
from datetime import date
from src.shared.domain.StockCode import StockCode
from src.market.domain.Stock import Stock, StockRepository
from src.market.domain.MarketData import Quote, QuoteRepository
from src.market.domain.FinancialData import FinancialReport, FinancialRepository


class TushareAdapter(StockRepository, QuoteRepository, FinancialRepository):
    """Tushare数据源适配器。需要token配置。"""

    def __init__(self, token: str) -> None:
        self._token = token
        self._pro = None

    def _get_pro(self):
        if self._pro is None:
            import tushare as ts
            ts.set_token(self._token)
            self._pro = ts.pro_api()
        return self._pro

    async def find(self, code: StockCode) -> Stock | None:
        try:
            pro = self._get_pro()
            df = pro.stock_basic(ts_code=str(code), fields="ts_code,name,list_date")
            if df.empty:
                return None
            row = df.iloc[0]
            listing = date.fromisoformat(str(row["list_date"])) if row["list_date"] else None
            return Stock(code=code, name=str(row["name"]), listing_date=listing)
        except Exception:
            return None

    async def search(self, keyword: str) -> list[Stock]:
        return []

    async def fetch_one(self, code: StockCode) -> Quote | None:
        try:
            pro = self._get_pro()
            df = pro.daily_basic(ts_code=str(code), trade_date=date.today().strftime("%Y%m%d"))
            if df.empty:
                return None
            row = df.iloc[0]
            return Quote(
                code=code,
                name="",
                price=float(row["close"]),
                pe_ttm=float(row["pe_ttm"]) if row.get("pe_ttm") else None,
                pb=float(row["pb"]) if row.get("pb") else None,
                market_cap=float(row["total_mv"]) / 1e4 if row.get("total_mv") else None,
                trade_date=date.today(),
            )
        except Exception:
            return None

    async def fetch_batch(self, codes: list[StockCode]) -> list[Quote]:
        try:
            pro = self._get_pro()
            ts_codes = ",".join(str(c) for c in codes)
            df = pro.daily_basic(ts_code=ts_codes, trade_date=date.today().strftime("%Y%m%d"))
            if df.empty:
                return []
            quotes: list[Quote] = []
            for _, row in df.iterrows():
                code = StockCode(str(row["ts_code"]))
                quotes.append(Quote(
                    code=code,
                    name="",
                    price=float(row["close"]),
                    pe_ttm=float(row["pe_ttm"]) if row.get("pe_ttm") else None,
                    pb=float(row["pb"]) if row.get("pb") else None,
                    market_cap=float(row["total_mv"]) / 1e4 if row.get("total_mv") else None,
                    trade_date=date.today(),
                ))
            return quotes
        except Exception:
            return []

    async def fetch(self, code: StockCode, periods: int = 4) -> list[FinancialReport]:
        return []

    async def fetch_batch(self, codes: list[StockCode], periods: int = 4) -> dict[StockCode, list[FinancialReport]]:
        return {}
