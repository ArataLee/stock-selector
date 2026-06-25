# src/cli/main.py
import typer
from src.bootstrap import AppContext

_app_ctx: AppContext | None = None


def get_app_context() -> AppContext:
    global _app_ctx
    if _app_ctx is None:
        _app_ctx = AppContext()
    return _app_ctx


app = typer.Typer(
    name="stock-selector",
    help="A股成长价值选股助手",
)


@app.callback()
def main(
    config_dir: str = typer.Option(
        None, "--config-dir", "-c",
        help="配置文件目录",
    ),
):
    global _app_ctx
    from src.bootstrap import bootstrap
    _app_ctx = bootstrap(config_dir)


from src.cli.commands.market import market_app  # noqa: E402

app.add_typer(market_app, name="market")


from src.cli.commands.screening import screening_app  # noqa: E402

app.add_typer(screening_app, name="screening")


from src.cli.commands.server import server_app  # noqa: E402

app.add_typer(server_app, name="server")


def run():
    app()


if __name__ == "__main__":
    run()
