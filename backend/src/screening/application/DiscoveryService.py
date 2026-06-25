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

        # 3. Score ALL candidates with LLM, return top N by composite score
        codes = [str(c) for c in candidates]
        outcome = await self._screen.screen_batch(codes)
        outcome.results = outcome.results[:count]
        return outcome

    async def _parse_query(self, query: str, count: int) -> list[str]:
        """Use LLM to expand sector query into specific search keywords."""
        prompt = f"""用户想找A股股票，请将用户的描述扩展为3-5个具体搜索关键词，用于在股票名称中匹配。

用户输入: {query}
期望推荐数量: {count}只

规则:
1. 关键词不应太宽泛（如"消费"太宽，应该扩展为"食品、白酒、家电、零售"等）
2. 关键词不应太长（2-4个字最佳，因为股票名称中通常包含这些词）
3. 如果有行业专属术语，直接使用（如"半导"比"半导体"更容易匹配到股票名）

示例:
- 用户"消费股" → 食品,白酒,家电,零售,服装
- 用户"新能源" → 锂电,光伏,风电,储能,新能
- 用户"半导体" → 半导,芯片,集成,电子
- 用户"医药" → 制药,生物,医疗,中药,药

请只输出关键词，用逗号分隔，最多5个。不要其他内容。"""

        messages = [{"role": "user", "content": prompt}]
        raw = ""
        async for token in self._llm.chat(messages):
            if token:
                raw += token
        keywords = [k.strip() for k in raw.replace("\n", ",").split(",") if k.strip()]
        return keywords[:5] if keywords else [query]

    async def _find_candidates(self, keywords: list[str], limit: int) -> list[StockCode]:
        """Find stocks matching sector keywords."""
        codes_set: set[str] = set()

        # Strategy 1: THS concept name → EM constituent stocks
        for kw in keywords:
            try:
                import akshare as ak
                concepts = ak.stock_board_concept_name_ths()
                if concepts is not None and not concepts.empty:
                    # Match concept names (exact or fuzzy on concept name)
                    for _, concept_row in concepts.iterrows():
                        concept_name = str(concept_row["name"])
                        if kw in concept_name:
                            try:
                                cons_df = ak.stock_board_concept_cons_em(symbol=concept_name)
                                if cons_df is not None and not cons_df.empty:
                                    for _, cr in cons_df.iterrows():
                                        raw = str(cr.get("代码", ""))
                                        if raw.isdigit() and len(raw) == 6:
                                            codes_set.add(raw)
                            except Exception:
                                continue
            except Exception:
                pass

        # Strategy 2: Try industry boards via EM
        if not codes_set:
            for kw in keywords:
                for fn_name in ["stock_board_industry_cons_em", "stock_board_concept_cons_em"]:
                    try:
                        import akshare as ak
                        fn = getattr(ak, fn_name)
                        df = fn(symbol=kw)
                        if df is not None and not df.empty:
                            for _, r in df.iterrows():
                                raw = str(r.get("代码", ""))
                                if raw.isdigit():
                                    codes_set.add(raw)
                    except Exception:
                        continue

        # Strategy 3: Name matching on Sina data (fallback, min 2 chars)
        if not codes_set:
            try:
                import akshare as ak
                df = ak.stock_zh_a_spot()
                for kw in keywords:
                    for _, r in df.iterrows():
                        name = str(r.get("名称", ""))
                        raw = str(r.get("代码", ""))
                        if len(raw) < 6:
                            continue
                        digits = raw[-6:]
                        if not digits.isdigit():
                            continue
                        # Exact match first
                        if kw in name:
                            codes_set.add(digits)
                        elif len(kw) >= 2:
                            # Fuzzy: try progressively shorter substrings, min 2 chars
                            for end in range(len(kw) - 1, 1, -1):
                                if kw[:end] in name:
                                    codes_set.add(digits)
                                    break
            except Exception:
                pass

        result: list[StockCode] = []
        for raw_code in list(codes_set)[:limit]:
            try:
                code = StockCode.parse(raw_code)
                result.append(code)
            except ValueError:
                continue
        return result
