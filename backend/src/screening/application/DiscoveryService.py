"""Stock discovery — natural language → sector filter → LLM scoring → recommendations."""
import asyncio
from src.shared.domain.StockCode import StockCode
from src.market.domain.MarketData import QuoteRepository
from src.market.domain.FinancialData import FinancialRepository
from src.llm.infrastructure.adapters.OpenAICompatAdapter import OpenAICompatAdapter
from src.screening.domain.Dimension import DEFAULT_DIMENSIONS
from src.screening.application.ScreenStockUseCase import ScreenStockUseCase, ScreeningOutcome


class DiscoveryService:
    def __init__(
        self,
        quote_repo: QuoteRepository,
        financial_repo: FinancialRepository,
        llm_adapter: OpenAICompatAdapter,
        screen_usecase: ScreenStockUseCase,
    ):
        self._quote_repo = quote_repo
        self._llm = llm_adapter
        self._screen = screen_usecase

    async def discover(self, query: str, count: int = 5) -> ScreeningOutcome:
        # 1. LLM parses query → sector keywords
        sector_keywords = await self._parse_query(query, count)

        # 2. Fetch stocks by industry/concept sectors
        candidates = await self._find_candidates(sector_keywords, count * 5)

        if not candidates:
            return ScreeningOutcome(errors=[f"未找到与'{', '.join(sector_keywords)}'相关的股票"])

        # 3. Score candidates with LLM
        codes = [str(c) for c in candidates[:count * 3]]  # Score top N*3, return top N
        outcome = await self._screen.screen_batch(codes)
        outcome.results = outcome.results[:count]
        return outcome

    async def _parse_query(self, query: str, count: int) -> list[str]:
        """Use LLM to extract industry/sector keywords from natural language."""
        prompt = f"""用户想找股票，请提取其中的行业、板块或概念关键词。

用户输入: {query}
期望推荐数量: {count}只

请只输出关键词，用逗号分隔，最多3个。
例如: 半导体,芯片,集成电路

只输出关键词，不要其他内容。"""

        messages = [{"role": "user", "content": prompt}]
        raw = ""
        async for token in self._llm.chat(messages):
            raw += token
        # Parse comma-separated keywords
        keywords = [k.strip() for k in raw.replace("\n", ",").split(",") if k.strip()]
        return keywords[:3] if keywords else [query]

    async def _find_candidates(self, keywords: list[str], limit: int) -> list[StockCode]:
        """Find stocks matching sector keywords using AKShare."""
        codes_set: set[str] = set()

        for kw in keywords:
            # Try as industry sector
            try:
                stocks = await self._sector_stocks(kw)
                codes_set.update(stocks)
            except Exception:
                pass

            # Try as concept sector
            try:
                stocks = await self._concept_stocks(kw)
                codes_set.update(stocks)
            except Exception:
                pass

        # Convert to StockCode, dedupe, limit
        result: list[StockCode] = []
        for raw_code in list(codes_set)[:limit]:
            try:
                code = StockCode.parse(raw_code)
                result.append(code)
            except ValueError:
                continue
        return result

    async def _sector_stocks(self, name: str) -> list[str]:
        """Get stocks in an industry sector via AKShare."""
        import akshare as ak
        df = ak.stock_board_industry_cons_em(symbol=name)
        if df is None or df.empty:
            raise ValueError(f"No stocks in sector: {name}")
        codes = []
        for _, r in df.iterrows():
            raw = str(r.get("代码", ""))
            if raw and raw.isdigit():
                codes.append(raw)
        return codes

    async def _concept_stocks(self, name: str) -> list[str]:
        """Get stocks in a concept sector via AKShare."""
        import akshare as ak
        df = ak.stock_board_concept_cons_em(symbol=name)
        if df is None or df.empty:
            raise ValueError(f"No stocks in concept: {name}")
        codes = []
        for _, r in df.iterrows():
            raw = str(r.get("代码", ""))
            if raw and raw.isdigit():
                codes.append(raw)
        return codes
