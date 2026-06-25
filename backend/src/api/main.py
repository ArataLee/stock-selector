from fastapi import FastAPI
from src.api.middleware.error_handler import register_error_handlers
from src.api.routes.market import router as market_router
from src.api.routes.screening import router as screening_router
from src.api.routes.llm import router as llm_router
from src.api.routes.user import router as user_router
from src.api.routes.config_routes import router as config_router
from src.api.routes.notification import router as notification_router


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

    app.include_router(market_router)
    app.include_router(screening_router)
    app.include_router(llm_router)
    app.include_router(user_router)
    app.include_router(config_router)
    app.include_router(notification_router)

    @app.get("/api/health")
    async def health():
        return {"status": "ok"}

    return app


app = create_app()
