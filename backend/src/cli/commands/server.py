import typer
import uvicorn

server_app = typer.Typer(help="服务器管理")


@server_app.command("start")
def start_server(
    host: str = typer.Option("127.0.0.1", "--host", "-h"),
    port: int = typer.Option(8000, "--port", "-p"),
    reload: bool = typer.Option(False, "--reload", "-r"),
):
    """启动Web API服务器"""
    uvicorn.run("src.api.main:app", host=host, port=port, reload=reload)
