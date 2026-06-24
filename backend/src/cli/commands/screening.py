# src/cli/commands/screening.py
import asyncio
import typer
from src.screening.domain.Dimension import DEFAULT_DIMENSIONS

screening_app = typer.Typer(help="选股筛选")


@screening_app.command("screen")
def screen(
    codes: list[str] = typer.Argument(..., help="股票代码列表，如 600001.SH 000001.SZ"),
    dimensions: str = typer.Option(
        "default", "--dimensions", "-d",
        help="评估维度: default(综合), financial(财务), industry(行业), valuation(估值)",
    ),
):
    """对指定股票进行成长价值评分"""
    from src.cli.main import get_app_context
    ctx = get_app_context()

    if ctx.provider_registry is None or ctx.provider_registry.default() is None:
        typer.echo("错误：未配置LLM。请先配置LLM provider。", err=True)
        raise typer.Exit(1)

    if dimensions == "default":
        dims = DEFAULT_DIMENSIONS
    else:
        dim_keys = dimensions.split(",")
        dims = [d for d in DEFAULT_DIMENSIONS if d.id in dim_keys]
        if not dims:
            typer.echo(f"未知维度: {dimensions}", err=True)
            raise typer.Exit(1)

    async def _run():
        results = await ctx.screen_usecase.screen_batch(codes, dims)

        if not results:
            typer.echo("未能获取任何评分结果。")
            return

        typer.echo(f"\n{'='*60}")
        typer.echo(f"  成长价值评估结果（共{len(results)}只）")
        typer.echo(f"{'='*60}\n")

        for i, r in enumerate(results, 1):
            tier_icon = {"不推荐": "🔴", "推荐": "🟡", "力荐": "🟢"}.get(r.tier.label, "")
            typer.echo(f"{i}. {tier_icon} {r.stock_name} ({r.stock_code})")
            typer.echo(f"   综合评分: {r.composite_score:.0f}  [{r.tier.label}]")

            if r.score_card.dimension_scores:
                dim_str = " | ".join(
                    f"{k}: {v:.0f}" for k, v in r.score_card.dimension_scores.items()
                )
                typer.echo(f"   各维度: {dim_str}")

            typer.echo(f"   理由: {r.reasoning[:200]}")
            typer.echo("")

    asyncio.run(_run())


@screening_app.command("analyze")
def analyze(
    code: str = typer.Argument(..., help="股票代码，如 600001.SH"),
):
    """深度分析单只股票"""
    from src.cli.main import get_app_context
    ctx = get_app_context()

    if ctx.provider_registry is None or ctx.provider_registry.default() is None:
        typer.echo("错误：未配置LLM。请先配置LLM provider。", err=True)
        raise typer.Exit(1)

    async def _run():
        result = await ctx.screen_usecase.screen_single(code)
        if result is None:
            typer.echo(f"无法获取 {code} 的数据。", err=True)
            return

        typer.echo(f"\n{'='*60}")
        typer.echo(f"  {result.stock_name} ({result.stock_code}) 深度分析")
        typer.echo(f"{'='*60}\n")
        typer.echo(f"综合评分: {result.composite_score:.0f}  [{result.tier.label}]\n")

        if result.score_card.dimension_scores:
            typer.echo("各维度评分:")
            for k, v in result.score_card.dimension_scores.items():
                bar = "█" * int(v / 5) + "░" * (20 - int(v / 5))
                typer.echo(f"  {k:12s} [{bar}] {v:.0f}")
            typer.echo("")

        typer.echo(f"推荐理由:\n{result.reasoning}\n")

    asyncio.run(_run())
