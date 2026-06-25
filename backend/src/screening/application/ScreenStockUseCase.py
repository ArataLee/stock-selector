import logging
from dataclasses import dataclass, field
from src.shared.domain.StockCode import StockCode
from src.market.domain.MarketData import QuoteRepository
from src.market.domain.FinancialData import FinancialRepository
from src.llm.domain.Prompt import BUILTIN_PROMPTS
from src.llm.infrastructure.adapters.OpenAICompatAdapter import OpenAICompatAdapter
from src.screening.domain.Dimension import Dimension, DEFAULT_DIMENSIONS
from src.screening.domain.ScreenResult import ScreenResult

logger = logging.getLogger(__name__)


@dataclass
class ScreeningOutcome:
    results: list[ScreenResult] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)  # codes with no data

    @property
    def count(self) -> int:
        return len(self.results)


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

    def _ensure_llm(self) -> None:
        try:
            self._llm._get_client()
        except RuntimeError as e:
            raise RuntimeError(
                "未配置LLM Provider。请在设置中配置DeepSeek、通义千问等大语言模型。"
            ) from e

    @staticmethod
    def _parse_code(raw: str) -> StockCode:
        """Parse stock code with smart format detection."""
        return StockCode.parse(raw)

    async def screen_single(self, code_str: str, dimensions: list[Dimension] | None = None) -> ScreenResult | None:
        code = self._parse_code(code_str)
        dims = dimensions or DEFAULT_DIMENSIONS

        quote = await self._quote_repo.fetch_one(code)
        if quote is None:
            logger.warning("No quote data for %s", code)
            return None

        reports = await self._financial_repo.fetch(code, periods=4)
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

        template = BUILTIN_PROMPTS["default_scoring"]
        score_card = await self._llm.score_stock(template, variables)

        return ScreenResult(
            stock_code=code,
            stock_name=quote.name,
            score_card=score_card,
        )

    async def screen_batch(
        self, code_strs: list[str], dimensions: list[Dimension] | None = None
    ) -> ScreeningOutcome:
        # Validate LLM availability upfront
        self._ensure_llm()

        # Parse codes with smart detection
        codes: list[StockCode] = []
        parse_errors: list[str] = []
        for s in code_strs:
            try:
                codes.append(self._parse_code(s))
            except ValueError as e:
                parse_errors.append(str(e))

        if not codes:
            return ScreeningOutcome(errors=parse_errors)

        dims = dimensions or DEFAULT_DIMENSIONS

        # Fetch quotes
        quotes = await self._quote_repo.fetch_quotes(codes)
        quote_map = {q.code: q for q in quotes}

        # Fetch financials
        fin_map = await self._financial_repo.fetch_financials(codes, periods=4)

        # Score each stock
        template = BUILTIN_PROMPTS["default_scoring"]
        dims_text = "\n".join(f"- {d.name}: {d.description}" for d in dims)

        results: list[ScreenResult] = []
        skipped: list[str] = []

        for code in codes:
            quote = quote_map.get(code)
            if quote is None:
                skipped.append(f"{code} — 无行情数据")
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
            except Exception as e:
                skipped.append(f"{code} — LLM评分失败: {e}")

        results.sort(key=lambda r: r.composite_score, reverse=True)

        return ScreeningOutcome(
            results=results,
            errors=parse_errors,
            skipped=skipped,
        )

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
