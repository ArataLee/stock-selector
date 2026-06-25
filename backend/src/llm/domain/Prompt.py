from dataclasses import dataclass, field


@dataclass
class PromptTemplate:
    template_id: str
    scenario: str
    content: str
    description: str = ""
    variables: list[str] = field(default_factory=list)


DEFAULT_SCORING_PROMPT = PromptTemplate(
    template_id="default_scoring",
    scenario="scoring",
    description="默认多维度综合评分模板",
    content="""你是一位专业的A股成长股投资分析师。请对以下股票进行多维度成长价值评估。

## 股票信息
- 代码: {stock_code}
- 名称: {stock_name}
- 最新价: {price}元
- PE(TTM): {pe_ttm}
- PB: {pb}
- 总市值: {market_cap}亿

## 近几期财务数据
{financial_data}

## 评估维度
{dimensions}

## 评分规则
请对每个维度打分（0-100分），然后给出综合评分（0-100分），并提供推荐理由。
评分标准：
- 0-60分：成长性不足，不推荐
- 60-80分：有一定成长价值，推荐
- 80-100分：成长价值突出，力荐

## 重要提示
reasoning字段末尾必须加上"建议仅供参考，不构成任何投资建议。"

## 输出格式（严格JSON）
```json
{{
  "dimension_scores": {{"维度名": 分数, ...}},
  "composite_score": 综合分数,
  "reasoning": "推荐理由，200字以内"
}}
```

请直接输出JSON，不要包含其他内容。""",
    variables=["stock_code", "stock_name", "price", "pe_ttm", "pb", "market_cap", "financial_data", "dimensions"],
)


DEFAULT_CHAT_PROMPT = PromptTemplate(
    template_id="default_chat",
    scenario="conversation",
    description="默认对话模板",
    content="""你是一位专业的A股投资顾问，擅长帮助投资新手分析股票的成长价值。
你可以：分析股票基本面、解读财务数据、评估成长潜力、回答选股相关问题。
请用通俗易懂的语言回答，避免过多专业术语。

当前上下文：
{context}

用户问题：{question}""",
    variables=["context", "question"],
)


BUILTIN_PROMPTS: dict[str, PromptTemplate] = {
    "default_scoring": DEFAULT_SCORING_PROMPT,
    "default_chat": DEFAULT_CHAT_PROMPT,
}
