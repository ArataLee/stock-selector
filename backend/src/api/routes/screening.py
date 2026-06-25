from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from src.api.schemas.screening import ScreeningRequest, ScreeningResponse, ScreenResultResponse, TaskStatusResponse
from src.api.deps import _cached_bootstrap
from src.screening.domain.Dimension import DEFAULT_DIMENSIONS

router = APIRouter(prefix="/api/screening", tags=["screening"])


class DiscoverRequest(BaseModel):
    query: str
    count: int = 5


@router.post("/tasks", response_model=ScreeningResponse)
async def create_screening(req: ScreeningRequest):
    ctx = _cached_bootstrap()

    if req.dimensions:
        dims = [d for d in DEFAULT_DIMENSIONS if d.id in req.dimensions]
    else:
        dims = DEFAULT_DIMENSIONS

    outcome = await ctx.screen_usecase.screen_batch(req.codes, dims)

    resp_results = [
        ScreenResultResponse(
            stock_code=str(r.stock_code),
            stock_name=r.stock_name,
            dimension_scores=r.score_card.dimension_scores,
            composite_score=r.composite_score,
            tier=r.tier.label,
            reasoning=r.reasoning,
        )
        for r in outcome.results
    ]

    return ScreeningResponse(
        task_id=0,
        results=resp_results,
        count=outcome.count,
        skipped=outcome.skipped,
        errors=outcome.errors,
    )


@router.get("/tasks/{task_id}/results", response_model=ScreeningResponse)
async def get_task_results(task_id: int):
    return ScreeningResponse(task_id=task_id, results=[], count=0, skipped=[], errors=[])


@router.post("/discover", response_model=ScreeningResponse)
async def discover_stocks(req: DiscoverRequest):
    """智能发现：自然语言描述 → 推荐股票"""
    ctx = _cached_bootstrap()
    from src.screening.application.DiscoveryService import DiscoveryService
    service = DiscoveryService(
        quote_repo=ctx.quote_router,
        financial_repo=ctx.financial_router,
        llm_adapter=ctx.llm_adapter,
        screen_usecase=ctx.screen_usecase,
    )
    outcome = await service.discover(req.query, req.count)

    resp_results = [
        ScreenResultResponse(
            stock_code=str(r.stock_code),
            stock_name=r.stock_name,
            dimension_scores=r.score_card.dimension_scores,
            composite_score=r.composite_score,
            tier=r.tier.label,
            reasoning=r.reasoning,
        )
        for r in outcome.results
    ]

    if outcome.errors:
        raise HTTPException(status_code=400, detail="; ".join(outcome.errors))

    return ScreeningResponse(
        task_id=0, results=resp_results, count=outcome.count,
        skipped=outcome.skipped, errors=outcome.errors,
    )


@router.post("/pre-screen")
async def pre_screen(universe: str = "all"):
    return {"message": "Pre-screen initiated", "universe": universe}
