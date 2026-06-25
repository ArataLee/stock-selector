from fastapi import FastAPI
from src.api.middleware.error_handler import register_error_handlers


def create_app() -> FastAPI:
    app = FastAPI(
        title="Stock Selector",
        description="A股成长价值选股助手",
        version="0.1.0",
    )
    register_error_handlers(app)

    @app.on_event("startup")
    async def startup():
        from src.shared.infrastructure.Database import init_db
        await init_db()

    @app.get("/api/health")
    async def health():
        return {"status": "ok"}

    return app


app = create_app()
