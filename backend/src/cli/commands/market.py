# src/cli/commands/market.py
import typer
import asyncio

market_app = typer.Typer(help="市场数据查询")


@market_app.command("quote")
def quote(
    code: str = typer.Argument(..., help="股票代码，如 600001.SH"),
):
    """查询实时行情"""
    from src.cli.main import get_app_context
    ctx = get_app_context()

    async def _run():
        svc = ctx.quote_service
        q = await svc.get_quote(code)
        if q is None:
            typer.echo(f"未找到股票行情: {code}")
            return
        typer.echo(f"股票: {q.name} ({q.code})")
        typer.echo(f"最新价: {q.price:.2f}元")
        if q.pe_ttm:
            typer.echo(f"PE(TTM): {q.pe_ttm:.1f}")
        if q.pb:
            typer.echo(f"PB: {q.pb:.2f}")
        if q.market_cap:
            typer.echo(f"总市值: {q.market_cap:.0f}亿")

    asyncio.run(_run())
