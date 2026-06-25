from fastapi import APIRouter, Depends, HTTPException
from src.api.schemas.market import QuoteResponse, FinancialReportResponse, StockInfoResponse
from src.api.deps import _cached_bootstrap
from src.shared.domain.StockCode import StockCode
from src.market.application.QuoteQueryService import QuoteQueryService

router = APIRouter(prefix="/api/market", tags=["market"])


@router.get("/stocks/{code}/quote", response_model=QuoteResponse)
async def get_stock_quote(code: str):
    ctx = _cached_bootstrap()
    svc = QuoteQueryService(ctx.quote_router)
    q = await svc.get_quote(code)
    if q is None:
        raise HTTPException(status_code=404, detail=f"Quote not found: {code}")
    return QuoteResponse(
        stock_code=str(q.code),
        stock_name=q.name,
        price=q.price,
        pe_ttm=q.pe_ttm,
        pb=q.pb,
        market_cap=q.market_cap,
        volume=q.volume,
    )


@router.get("/stocks/{code}/financials", response_model=list[FinancialReportResponse])
async def get_stock_financials(code: str, periods: int = 4):
    ctx = _cached_bootstrap()
    stock_code = StockCode(code)
    reports = await ctx.financial_router.fetch(stock_code, periods)
    return [
        FinancialReportResponse(
            period=r.period,
            revenue_yoy=r.revenue_yoy,
            profit_yoy=r.profit_yoy,
            roe=r.roe,
            gross_margin=r.gross_margin,
            net_margin=r.net_margin,
        )
        for r in reports
    ]
