from fastapi import APIRouter, HTTPException
from src.api.schemas.screening import ScreeningRequest, ScreeningResponse, ScreenResultResponse, TaskStatusResponse
from src.api.deps import _cached_bootstrap
from src.screening.domain.Dimension import DEFAULT_DIMENSIONS

router = APIRouter(prefix="/api/screening", tags=["screening"])


@router.post("/tasks", response_model=ScreeningResponse)
async def create_screening(req: ScreeningRequest):
    ctx = _cached_bootstrap()
    if ctx.provider_registry.default() is None:
        raise HTTPException(status_code=400, detail="No LLM provider configured")

    if req.dimensions:
        dims = [d for d in DEFAULT_DIMENSIONS if d.id in req.dimensions]
    else:
        dims = DEFAULT_DIMENSIONS

    results = await ctx.screen_usecase.screen_batch(req.codes, dims)

    resp_results = [
        ScreenResultResponse(
            stock_code=str(r.stock_code),
            stock_name=r.stock_name,
            dimension_scores=r.score_card.dimension_scores,
            composite_score=r.composite_score,
            tier=r.tier.label,
            reasoning=r.reasoning,
        )
        for r in results
    ]

    return ScreeningResponse(task_id=0, results=resp_results, count=len(resp_results))


@router.get("/tasks/{task_id}/results", response_model=ScreeningResponse)
async def get_task_results(task_id: int):
    return ScreeningResponse(task_id=task_id, results=[], count=0)


@router.post("/pre-screen")
async def pre_screen(universe: str = "all"):
    return {"message": "Pre-screen initiated", "universe": universe}
