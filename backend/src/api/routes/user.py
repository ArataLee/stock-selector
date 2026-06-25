from fastapi import APIRouter
from src.api.schemas.user import UserPreferencesRequest, WatchlistAddRequest
from src.shared.domain.StockCode import StockCode

router = APIRouter(prefix="/api/user", tags=["user"])


@router.get("/watchlist")
async def get_watchlist():
    return {"items": []}


@router.post("/watchlist")
async def add_to_watchlist(req: WatchlistAddRequest):
    code = StockCode(req.stock_code)
    return {"stock_code": str(code), "status": "added"}


@router.delete("/watchlist/{code}")
async def remove_from_watchlist(code: str):
    return {"stock_code": code, "status": "removed"}


@router.get("/profile")
async def get_profile():
    return {
        "default_dimensions": ["financial", "industry", "valuation"],
        "default_universe": "all",
        "batch_size": 20,
    }


@router.put("/profile/preferences")
async def update_preferences(req: UserPreferencesRequest):
    return {"status": "updated"}
