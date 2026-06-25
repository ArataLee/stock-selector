from datetime import date
import logging
from src.shared.domain.StockCode import StockCode
from src.market.domain.Stock import Stock, StockRepository
from src.market.domain.MarketData import Quote, QuoteRepository
from src.market.domain.FinancialData import FinancialReport, FinancialRepository

logger = logging.getLogger(__name__)


class AKShareAdapter(StockRepository, QuoteRepository, FinancialRepository):
    """AKShare数据源适配器，免费开源，开箱即用。

    内部多源降级：
    - 行情: 新浪 → 东财（东财API可能被限频）
    - 财务: 同花顺 → 新浪
    - 基本信息: 东财 → 新浪
    """

    # ── Stock info ──────────────────────────────────────────────

    async def find(self, code: StockCode) -> Stock | None:
        for name, fn in [("em", self._find_em), ("sina", self._find_sina)]:
            try:
                result = await fn(code)
                if result is not None:
                    return result
            except Exception:
                logger.debug("AKShare find from %s failed for %s", name, code)
        return None

    async def _find_em(self, code: StockCode) -> Stock | None:
        import akshare as ak
        info = ak.stock_individual_info_em(symbol=code.digits)
        if info is None or info.empty:
            raise ValueError("Empty response")
        name_row = info[info["item"] == "股票简称"]
        name = name_row["value"].iloc[0] if not name_row.empty else code.digits
        return Stock(code=code, name=str(name))

    async def _find_sina(self, code: StockCode) -> Stock | None:
        import akshare as ak
        info = ak.stock_individual_info_sw(symbol=code.digits)
        if info is None or info.empty:
            raise ValueError("Empty response")
        name_row = info[info["item"] == "股票简称"]
        name = name_row["value"].iloc[0] if not name_row.empty else code.digits
        return Stock(code=code, name=str(name))

    async def search(self, keyword: str) -> list[Stock]:
        return []

    # ── Quotes (行情) ───────────────────────────────────────────
    # 新浪优先（东财经常被限频），东财兜底

    async def fetch_one(self, code: StockCode) -> Quote | None:
        for name, fn in [
            ("sina", self._fetch_quote_sina),
            ("em", self._fetch_quote_em),
        ]:
            try:
                result = await fn(code)
                if result is not None:
                    return result
            except Exception:
                logger.debug("AKShare quote from %s failed for %s", name, code)
        return None

    async def fetch_quotes(self, codes: list[StockCode]) -> list[Quote]:
        for name, fn in [
            ("sina", self._fetch_quotes_sina),
            ("em", self._fetch_quotes_em),
        ]:
            try:
                result = await fn(codes)
                if result:
                    return result
            except Exception:
                logger.debug("AKShare batch quotes from %s failed", name)
        return []

    # -- 新浪行情 (主) --

    async def _fetch_quote_sina(self, code: StockCode) -> Quote | None:
        import akshare as ak
        df = ak.stock_zh_a_spot()
        sina_code = _to_sina_code(code)  # sh600519
        row = df[df["代码"] == sina_code]
        if row.empty:
            return None
        r = row.iloc[0]
        return Quote(
            code=code,
            name=str(r.get("名称", code.digits)),
            price=float(r.get("最新价", 0)),
            pe_ttm=None,
            pb=None,
            market_cap=None,
            trade_date=date.today(),
        )

    async def _fetch_quotes_sina(self, codes: list[StockCode]) -> list[Quote]:
        import akshare as ak
        df = ak.stock_zh_a_spot()
        code_map = {_to_sina_code(c): c for c in codes}
        quotes: list[Quote] = []
        for _, r in df.iterrows():
            sc = str(r.get("代码", ""))
            if sc in code_map:
                qcode = code_map[sc]
                quotes.append(Quote(
                    code=qcode,
                    name=str(r.get("名称", qcode.digits)),
                    price=float(r.get("最新价", 0)),
                    pe_ttm=None,
                    pb=None,
                    market_cap=None,
                    trade_date=date.today(),
                ))
        if not quotes:
            raise ValueError("No matching quotes in Sina response")
        return quotes

    # -- 东财行情 (兜底) --

    async def _fetch_quote_em(self, code: StockCode) -> Quote | None:
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
            pe_ttm=float(r["市盈率-动态"]) if self._safe_get(r, "市盈率-动态") else None,
            pb=float(r["市净率"]) if self._safe_get(r, "市净率") else None,
            market_cap=float(r["总市值"]) / 1e8 if self._safe_get(r, "总市值") else None,
            volume=float(r["成交量"]) if self._safe_get(r, "成交量") else None,
            trade_date=date.today(),
        )

    async def _fetch_quotes_em(self, codes: list[StockCode]) -> list[Quote]:
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
                    pe_ttm=float(r["市盈率-动态"]) if self._safe_get(r, "市盈率-动态") else None,
                    pb=float(r["市净率"]) if self._safe_get(r, "市净率") else None,
                    market_cap=float(r["总市值"]) / 1e8 if self._safe_get(r, "总市值") else None,
                    trade_date=date.today(),
                ))
        if not quotes:
            raise ValueError("No matching quotes in East Money response")
        return quotes

    # ── Financial data (财务数据) ────────────────────────────────

    async def fetch(self, code: StockCode, periods: int = 4) -> list[FinancialReport]:
        for name, fn in [("ths", self._fetch_financials_ths), ("sina", self._fetch_financials_sina)]:
            try:
                result = await fn(code, periods)
                if result:
                    return result
            except Exception:
                logger.debug("AKShare financials from %s failed for %s", name, code)
        return []

    async def fetch_financials(self, codes: list[StockCode], periods: int = 4) -> dict[StockCode, list[FinancialReport]]:
        result: dict[StockCode, list[FinancialReport]] = {}
        for code in codes:
            reports = await self.fetch(code, periods)
            if reports:
                result[code] = reports
        return result

    # -- 同花顺财务 --

    async def _fetch_financials_ths(self, code: StockCode, periods: int) -> list[FinancialReport]:
        import akshare as ak
        df = ak.stock_financial_abstract_ths(symbol=code.digits, indicator="按报告期")
        if df is None or df.empty:
            raise ValueError("Empty THS financial response")
        reports: list[FinancialReport] = []
        for _, r in df.iloc[::-1].head(periods).iterrows():
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

    # -- 新浪财务 --

    async def _fetch_financials_sina(self, code: StockCode, periods: int) -> list[FinancialReport]:
        import akshare as ak
        df = ak.stock_financial_abstract(symbol=code.digits)
        if df is None or df.empty:
            raise ValueError("Empty Sina financial response")
        reports: list[FinancialReport] = []
        for _, r in df.iloc[::-1].head(periods).iterrows():
            reports.append(FinancialReport(
                code=code,
                period=str(r.get("报告期", r.get("日期", ""))),
                revenue_yoy=self._safe_float(r.get("营业总收入同比增长", r.get("营业收入同比增长"))),
                profit_yoy=self._safe_float(r.get("净利润同比增长", r.get("归母净利润同比增长"))),
                roe=self._safe_float(r.get("净资产收益率", r.get("ROE"))),
                gross_margin=self._safe_float(r.get("销售毛利率", r.get("毛利率"))),
                net_margin=self._safe_float(r.get("销售净利率", r.get("净利率"))),
            ))
        return reports

    # ── Helpers ─────────────────────────────────────────────────

    @staticmethod
    def _safe_float(value) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _safe_get(series, key) -> bool:
        try:
            val = series[key]
            if val is None:
                return False
            import pandas as pd
            if pd.isna(val):
                return False
            return True
        except (KeyError, IndexError):
            return False


def _to_sina_code(code: StockCode) -> str:
    """Convert StockCode to Sina format: sh600519, sz000001, bj830001."""
    return f"{code.market.value.lower()}{code.digits}"
