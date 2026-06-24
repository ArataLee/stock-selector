from src.shared.domain.StockCode import StockCode
from src.market.domain.MarketData import QuoteRepository
from src.market.domain.FinancialData import FinancialRepository
from src.llm.domain.Prompt import BUILTIN_PROMPTS
from src.llm.domain.Analysis import ScoreCard
from src.llm.infrastructure.adapters.OpenAICompatAdapter import OpenAICompatAdapter
from src.screening.domain.Dimension import Dimension, DEFAULT_DIMENSIONS
from src.screening.domain.ScreenResult import ScreenResult


class ScreenStockUseCase:
    def __init__(
        self,
        quote_repo: QuoteRepository,
        financial_repo: FinancialRepository,
        llm_adapter: OpenAICompatAdapter,
    ) -> None:
        self._quote_repo = quote_repo
        self._financial_repo = financial_repo
        self._llm = llm_adapter

    async def screen_single(self, code_str: str, dimensions: list[Dimension] | None = None) -> ScreenResult | None:
        code = StockCode(code_str)
        dims = dimensions or DEFAULT_DIMENSIONS

        # 1. 获取行情
        quote = await self._quote_repo.fetch_one(code)
        if quote is None:
            return None

        # 2. 获取财务数据
        reports = await self._financial_repo.fetch(code, periods=4)

        # 3. 构建Prompt变量
        fin_text = self._format_financials(reports)
        dims_text = "\n".join(f"- {d.name}: {d.description}" for d in dims)

        variables = {
            "stock_code": str(code),
            "stock_name": quote.name,
            "price": f"{quote.price:.2f}",
            "pe_ttm": f"{quote.pe_ttm:.1f}" if quote.pe_ttm else "N/A",
            "pb": f"{quote.pb:.2f}" if quote.pb else "N/A",
            "market_cap": f"{quote.market_cap:.0f}" if quote.market_cap else "N/A",
            "financial_data": fin_text or "暂无财务数据",
            "dimensions": dims_text,
        }

        # 4. LLM打分
        template = BUILTIN_PROMPTS["default_scoring"]
        score_card = await self._llm.score_stock(template, variables)

        return ScreenResult(
            stock_code=code,
            stock_name=quote.name,
            score_card=score_card,
        )

    async def screen_batch(self, code_strs: list[str], dimensions: list[Dimension] | None = None) -> list[ScreenResult]:
        codes = [StockCode(s) for s in code_strs]
        dims = dimensions or DEFAULT_DIMENSIONS

        # 1. 批量获取行情
        quotes = await self._quote_repo.fetch_batch(codes)
        quote_map = {q.code: q for q in quotes}

        # 2. 批量获取财务数据
        fin_map = await self._financial_repo.fetch_batch(codes, periods=4)

        # 3. 逐个LLM打分
        template = BUILTIN_PROMPTS["default_scoring"]
        dims_text = "\n".join(f"- {d.name}: {d.description}" for d in dims)

        results: list[ScreenResult] = []
        for code in codes:
            quote = quote_map.get(code)
            if quote is None:
                continue

            reports = fin_map.get(code, [])
            fin_text = self._format_financials(reports)

            variables = {
                "stock_code": str(code),
                "stock_name": quote.name,
                "price": f"{quote.price:.2f}",
                "pe_ttm": f"{quote.pe_ttm:.1f}" if quote.pe_ttm else "N/A",
                "pb": f"{quote.pb:.2f}" if quote.pb else "N/A",
                "market_cap": f"{quote.market_cap:.0f}" if quote.market_cap else "N/A",
                "financial_data": fin_text or "暂无财务数据",
                "dimensions": dims_text,
            }

            try:
                score_card = await self._llm.score_stock(template, variables)
                results.append(ScreenResult(
                    stock_code=code,
                    stock_name=quote.name,
                    score_card=score_card,
                ))
            except Exception:
                continue

        # 4. 按综合评分降序
        results.sort(key=lambda r: r.composite_score, reverse=True)
        return results

    @staticmethod
    def _format_financials(reports) -> str:
        if not reports:
            return "暂无财务数据"
        lines = []
        for r in reports:
            parts = [f"  {r.period}:"]
            if r.revenue_yoy is not None:
                parts.append(f"营收同比{r.revenue_yoy:.1f}%")
            else:
                parts.append("营收同比N/A")
            if r.profit_yoy is not None:
                parts.append(f"净利同比{r.profit_yoy:.1f}%")
            else:
                parts.append("净利同比N/A")
            if r.roe is not None:
                parts.append(f"ROE={r.roe:.1f}%")
            else:
                parts.append("ROE=N/A")
            if r.gross_margin is not None:
                parts.append(f"毛利率={r.gross_margin:.1f}%")
            lines.append(" ".join(parts))
        return "\n".join(lines)
