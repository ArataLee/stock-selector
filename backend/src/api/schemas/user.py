from pydantic import BaseModel

class UserPreferencesRequest(BaseModel):
    default_dimensions: list[str] | None = None
    default_universe: str | None = None
    batch_size: int | None = None

class WatchlistAddRequest(BaseModel):
    stock_code: str
