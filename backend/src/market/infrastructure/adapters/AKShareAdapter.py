from datetime import date
from src.shared.domain.StockCode import StockCode
from src.market.domain.Stock import Stock, StockRepository
from src.market.domain.MarketData import Quote, QuoteRepository
from src.market.domain.FinancialData import FinancialReport, FinancialRepository


class AKShareAdapter(StockRepository, QuoteRepository, FinancialRepository):
    """AKShare数据源适配器。免费开源，开箱即用。"""

    async def find(self, code: StockCode) -> Stock | None:
        try:
            import akshare as ak
            info = ak.stock_individual_info_em(symbol=code.digits)
            if info is None or info.empty:
                return None
            name_row = info[info["item"] == "股票简称"]
            name = name_row["value"].iloc[0] if not name_row.empty else code.digits
            return Stock(code=code, name=str(name))
        except Exception:
            return None

    async def search(self, keyword: str) -> list[Stock]:
        # AKShare没有直接搜索接口，通过全量列表过滤
        return []

    async def fetch_one(self, code: StockCode) -> Quote | None:
        try:
            import akshare as ak
            df = ak.stock_zh_a_spot_em()
            row = df[df["代码"] == code.digits]
            if row.empty:
                return None
            r = row.iloc[0]
            return Quote(
                code=code,
                name=str(r.get("名称", code.digits)),
                price=float(r.get("最新价", 0)),
                pe_ttm=float(r["市盈率-动态"]) if r.get("市盈率-动态") else None,
                pb=float(r["市净率"]) if r.get("市净率") else None,
                market_cap=float(r["总市值"]) / 1e8 if r.get("总市值") else None,
                volume=float(r["成交量"]) if r.get("成交量") else None,
                trade_date=date.today(),
            )
        except Exception:
            return None

    async def fetch_batch(self, codes: list[StockCode]) -> list[Quote]:
        try:
            import akshare as ak
            df = ak.stock_zh_a_spot_em()
            code_set = {c.digits for c in codes}
            quotes: list[Quote] = []
            for _, r in df.iterrows():
                if r["代码"] in code_set:
                    qcode = next(c for c in codes if c.digits == r["代码"])
                    quotes.append(Quote(
                        code=qcode,
                        name=str(r.get("名称", qcode.digits)),
                        price=float(r.get("最新价", 0)),
                        pe_ttm=float(r["市盈率-动态"]) if r.get("市盈率-动态") else None,
                        pb=float(r["市净率"]) if r.get("市净率") else None,
                        market_cap=float(r["总市值"]) / 1e8 if r.get("总市值") else None,
                        trade_date=date.today(),
                    ))
            return quotes
        except Exception:
            return []

    async def fetch(self, code: StockCode, periods: int = 4) -> list[FinancialReport]:
        try:
            import akshare as ak
            df = ak.stock_financial_abstract_ths(symbol=code.digits, indicator="按报告期")
            if df is None or df.empty:
                return []
            reports: list[FinancialReport] = []
            for _, r in df.head(periods).iterrows():
                reports.append(FinancialReport(
                    code=code,
                    period=str(r.get("报告期", "")),
                    revenue_yoy=self._safe_float(r.get("营业总收入同比增长率")),
                    profit_yoy=self._safe_float(r.get("归母净利润同比增长率")),
                    roe=self._safe_float(r.get("净资产收益率")),
                    gross_margin=self._safe_float(r.get("销售毛利率")),
                    net_margin=self._safe_float(r.get("销售净利率")),
                ))
            return reports
        except Exception:
            return []

    async def fetch_batch(self, codes: list[StockCode], periods: int = 4) -> dict[StockCode, list[FinancialReport]]:
        result: dict[StockCode, list[FinancialReport]] = {}
        for code in codes:
            reports = await self.fetch(code, periods)
            if reports:
                result[code] = reports
        return result

    @staticmethod
    def _safe_float(value) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
