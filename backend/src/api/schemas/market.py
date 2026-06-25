from pydantic import BaseModel

class QuoteResponse(BaseModel):
    stock_code: str
    stock_name: str
    price: float
    pe_ttm: float | None = None
    pb: float | None = None
    market_cap: float | None = None
    volume: float | None = None

class FinancialReportResponse(BaseModel):
    period: str
    revenue_yoy: float | None = None
    profit_yoy: float | None = None
    roe: float | None = None
    gross_margin: float | None = None
    net_margin: float | None = None

class StockInfoResponse(BaseModel):
    stock_code: str
    stock_name: str
