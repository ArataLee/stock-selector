from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from src.api.schemas.screening import ScreenResultResponse
from src.api.deps import _cached_bootstrap

router = APIRouter(prefix="/api/llm", tags=["llm"])


@router.post("/score/{stock_code}", response_model=ScreenResultResponse)
async def score_single(stock_code: str):
    ctx = _cached_bootstrap()
    if ctx.provider_registry.default() is None:
        raise HTTPException(status_code=400, detail="No LLM provider configured")

    result = await ctx.screen_usecase.screen_single(stock_code)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Cannot score: {stock_code}")

    return ScreenResultResponse(
        stock_code=str(result.stock_code),
        stock_name=result.stock_name,
        dimension_scores=result.score_card.dimension_scores,
        composite_score=result.composite_score,
        tier=result.tier.label,
        reasoning=result.reasoning,
    )


@router.post("/chat")
async def chat(message: dict):
    ctx = _cached_bootstrap()
    if ctx.provider_registry.default() is None:
        raise HTTPException(status_code=400, detail="No LLM provider configured")

    messages = [{"role": "user", "content": message.get("content", "")}]

    async def stream():
        async for token in ctx.llm_adapter.chat(messages):
            yield f"data: {token}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")


@router.post("/reports/generate")
async def generate_report(stocks_data: list[dict]):
    ctx = _cached_bootstrap()
    if ctx.provider_registry.default() is None:
        raise HTTPException(status_code=400, detail="No LLM provider configured")

    report = await ctx.llm_adapter.generate_report(stocks_data)
    return {"report": report}
