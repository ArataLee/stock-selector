from pydantic import BaseModel

class ScreeningRequest(BaseModel):
    codes: list[str]
    dimensions: list[str] | None = None

class ScreenResultResponse(BaseModel):
    stock_code: str
    stock_name: str
    dimension_scores: dict[str, float]
    composite_score: float
    tier: str
    reasoning: str

class ScreeningResponse(BaseModel):
    task_id: int
    results: list[ScreenResultResponse]
    count: int
    skipped: list[str] = []
    errors: list[str] = []

class PreScreenRequest(BaseModel):
    universe: str = "all"

class TaskStatusResponse(BaseModel):
    id: int
    universe: str
    status: str
    result_count: int
    created_at: str
