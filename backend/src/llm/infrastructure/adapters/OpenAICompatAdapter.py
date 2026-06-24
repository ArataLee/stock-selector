import json
import re
from src.llm.domain.ModelProvider import ProviderConfig, ProviderRegistry
from src.llm.domain.Scenario import ScenarioType
from src.llm.domain.Prompt import PromptTemplate, BUILTIN_PROMPTS
from src.llm.domain.Analysis import ScoreCard
from src.llm.infrastructure.clients.LLMClient import LLMClient


class OpenAICompatAdapter:
    def __init__(self, registry: ProviderRegistry) -> None:
        self._registry = registry
        self._clients: dict[str, LLMClient] = {}

    def _get_client(self, provider_id: str | None = None) -> LLMClient:
        if provider_id:
            cfg = self._registry.find(provider_id)
        else:
            cfg = self._registry.default()
        if cfg is None:
            raise RuntimeError("No LLM provider configured. Please configure one in settings.")
        if cfg.id not in self._clients:
            self._clients[cfg.id] = LLMClient(cfg)
        return self._clients[cfg.id]

    async def score_stock(self, prompt_template: PromptTemplate, variables: dict, provider_id: str | None = None) -> ScoreCard:
        client = self._get_client(provider_id)
        content = prompt_template.content.format(**variables)
        messages = [{"role": "user", "content": content}]

        raw_response = await client.chat(messages, temperature=0.3, max_tokens=1024)
        return self._extract_score_card(raw_response)

    async def score_stocks_batch(
        self,
        prompt_template: PromptTemplate,
        variables_list: list[dict],
        provider_id: str | None = None,
    ) -> list[ScoreCard | None]:
        results: list[ScoreCard | None] = []
        for variables in variables_list:
            try:
                card = await self.score_stock(prompt_template, variables, provider_id)
                results.append(card)
            except Exception:
                results.append(None)
        return results

    async def chat(self, messages: list[dict], provider_id: str | None = None):
        client = self._get_client(provider_id)
        async for token in client.chat_stream(messages):
            yield token

    async def generate_report(self, stocks_data: list[dict], provider_id: str | None = None) -> str:
        client = self._get_client(provider_id)
        stock_summaries = "\n".join(
            f"- {s['name']}({s['code']}): 综合评分{s['score']}, {s['tier']}, {s['reasoning'][:100]}"
            for s in stocks_data
        )
        prompt = f"""请根据以下A股成长股筛选结果，生成一份简洁的投资分析报告。

## 筛选结果
{stock_summaries}

## 要求
1. 先总体概述筛选结果
2. 分析评分最高的3-5只股票
3. 给出风险提示（面向投资新手）
4. 使用Markdown格式，500字以内"""

        messages = [{"role": "user", "content": prompt}]
        return await client.chat(messages, temperature=0.5, max_tokens=2000)

    def _extract_score_card(self, raw: str) -> ScoreCard:
        # Try to extract JSON from response
        json_match = re.search(r'\{[\s\S]*\}', raw)
        if json_match:
            data = json.loads(json_match.group())
            return ScoreCard.from_llm_output(data)

        # Retry: if no JSON found, try a stricter approach
        raise ValueError(f"Failed to extract ScoreCard from LLM response: {raw[:200]}...")

    async def close(self) -> None:
        for client in self._clients.values():
            await client.close()
