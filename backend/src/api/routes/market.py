from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from src.api.schemas.market import QuoteResponse, FinancialReportResponse, StockInfoResponse
from src.api.deps import _cached_bootstrap
from src.shared.domain.StockCode import StockCode
from src.market.application.QuoteQueryService import QuoteQueryService

router = APIRouter(prefix="/api/market", tags=["market"])


@router.get("/status")
async def market_status():
    """返回当前A股市场状态（基于交易日历）。"""
    today = date.today()

    # Weekend check (fast path)
    if today.weekday() >= 5:
        return {"status": "休市", "detail": "周末休市"}

    # Check trading calendar via AKShare
    try:
        import akshare as ak
        df = ak.tool_trade_date_hist_sina()
        trade_dates = set(str(d) for d in df["trade_date"].values)
        today_str = today.strftime("%Y%m%d")
        if today_str not in trade_dates:
            return {"status": "休市", "detail": "节假日休市"}
    except Exception:
        pass  # fallback to time-based check below

    # Time-of-day check
    now_h = date.today()  # placeholder — actual time check done server-side
    from datetime import datetime
    now = datetime.now()
    t = now.hour * 60 + now.minute

    if t < 9 * 60 + 30:
        return {"status": "盘前", "detail": "等待开盘"}
    if t < 11 * 60 + 30:
        return {"status": "交易中", "detail": "上午盘"}
    if t < 13 * 60:
        return {"status": "午间休市", "detail": "11:30-13:00"}
    if t < 15 * 60:
        return {"status": "交易中", "detail": "下午盘"}
    return {"status": "已闭市", "detail": "今日交易结束"}


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
