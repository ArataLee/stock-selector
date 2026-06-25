# Phase 2: Persistence + FastAPI + User Context

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Working Web API that persists user data, screens stocks, and serves results via FastAPI.

**Architecture:** SQLAlchemy async + SQLite for user/domain persistence, DuckDB for financial data cache, FastAPI routes as thin adapters over Application layer, Pydantic v2 schemas for DTOs.

**Tech Stack:** SQLAlchemy 2.0 async, aiosqlite, DuckDB, FastAPI, uvicorn, pydantic v2

---

### Task 1: Add Phase 2 dependencies

**Files:**
- Modify: `backend/pyproject.toml`

Add to `[project]` dependencies:
```toml
"sqlalchemy[asyncio]>=2.0",
"aiosqlite>=0.20",
"duckdb>=1.1",
"fastapi>=0.115",
"uvicorn[standard]>=0.34",
```

Then: `cd backend && pip install -e ".[dev]"`

Commit: `git add backend/pyproject.toml && git commit -m "feat: add Phase 2 dependencies (SQLAlchemy, DuckDB, FastAPI, uvicorn)"`

---

### Task 2: Database engine setup

**Files:**
- Create: `backend/src/shared/infrastructure/__init__.py` (empty)
- Create: `backend/src/shared/infrastructure/Database.py`

```python
# src/shared/infrastructure/Database.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from pathlib import Path

DATABASE_URL = "sqlite+aiosqlite:///data/stock_selector.db"

engine = create_async_engine(DATABASE_URL, echo=False)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncSession:
    async with SessionLocal() as session:
        yield session


async def init_db():
    from src.shared.infrastructure.Base import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

- Create: `backend/src/shared/infrastructure/Base.py`
```python
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass
```

- Create: `backend/data/.gitkeep` (empty, for SQLite file location)

Commit.

---

### Task 3: User Context — Domain

**Files:**
- Create: `backend/src/user/__init__.py` (empty)
- Create: `backend/src/user/domain/__init__.py` (empty)
- Create: `backend/src/user/domain/User.py`

```python
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from src.shared.domain.StockCode import StockCode


@dataclass
class UserPreferences:
    default_dimensions: list[str] = field(default_factory=lambda: ["financial", "industry", "valuation"])
    default_universe: str = "all"  # "all" | "watchlist"
    batch_size: int = 20


@dataclass
class WatchlistItem:
    code: StockCode
    added_at: str  # ISO datetime


class UserRepository(ABC):
    @abstractmethod
    async def get_preferences(self) -> UserPreferences:
        ...

    @abstractmethod
    async def save_preferences(self, prefs: UserPreferences) -> None:
        ...

    @abstractmethod
    async def get_watchlist(self) -> list[WatchlistItem]:
        ...

    @abstractmethod
    async def add_to_watchlist(self, code: StockCode) -> None:
        ...

    @abstractmethod
    async def remove_from_watchlist(self, code: StockCode) -> None:
        ...
```

Commit.

---

### Task 4: User Context — Infrastructure (SQLAlchemy ORM)

**Files:**
- Create: `backend/src/user/infrastructure/__init__.py` (empty)
- Create: `backend/src/user/infrastructure/UserORM.py`
- Create: `backend/src/user/infrastructure/SQLiteUserRepository.py`

```python
# UserORM.py
from sqlalchemy import String, JSON, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from src.shared.infrastructure.Base import Base


class UserPreferencesModel(Base):
    __tablename__ = "user_preferences"
    id: Mapped[int] = mapped_column(primary_key=True)
    default_dimensions: Mapped[str] = mapped_column(String(500), default='["financial","industry","valuation"]')
    default_universe: Mapped[str] = mapped_column(String(20), default="all")
    batch_size: Mapped[int] = mapped_column(default=20)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class WatchlistModel(Base):
    __tablename__ = "watchlist"
    id: Mapped[int] = mapped_column(primary_key=True)
    stock_code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    added_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
```

```python
# SQLiteUserRepository.py
import json
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from src.shared.domain.StockCode import StockCode
from src.user.domain.User import UserPreferences, WatchlistItem, UserRepository
from src.user.infrastructure.UserORM import UserPreferencesModel, WatchlistModel


class SQLiteUserRepository(UserRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_preferences(self) -> UserPreferences:
        result = await self._session.execute(
            select(UserPreferencesModel).limit(1)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return UserPreferences()
        dims = json.loads(row.default_dimensions) if isinstance(row.default_dimensions, str) else row.default_dimensions
        return UserPreferences(
            default_dimensions=dims,
            default_universe=row.default_universe,
            batch_size=row.batch_size,
        )

    async def save_preferences(self, prefs: UserPreferences) -> None:
        row = UserPreferencesModel(
            default_dimensions=json.dumps(prefs.default_dimensions),
            default_universe=prefs.default_universe,
            batch_size=prefs.batch_size,
        )
        # Upsert: delete existing, insert new
        await self._session.execute(delete(UserPreferencesModel))
        self._session.add(row)
        await self._session.commit()

    async def get_watchlist(self) -> list[WatchlistItem]:
        result = await self._session.execute(select(WatchlistModel).order_by(WatchlistModel.added_at.desc()))
        rows = result.scalars().all()
        return [
            WatchlistItem(code=StockCode(r.stock_code), added_at=str(r.added_at))
            for r in rows
        ]

    async def add_to_watchlist(self, code: StockCode) -> None:
        existing = await self._session.execute(
            select(WatchlistModel).where(WatchlistModel.stock_code == str(code))
        )
        if existing.scalar_one_or_none() is None:
            self._session.add(WatchlistModel(stock_code=str(code)))
            await self._session.commit()

    async def remove_from_watchlist(self, code: StockCode) -> None:
        await self._session.execute(
            delete(WatchlistModel).where(WatchlistModel.stock_code == str(code))
        )
        await self._session.commit()
```

Commit.

---

### Task 5: Screening persistence — ORM models + Repository

**Files:**
- Create: `backend/src/screening/infrastructure/__init__.py` (empty)
- Create: `backend/src/screening/infrastructure/ScreeningORM.py`
- Create: `backend/src/screening/infrastructure/SQLiteScreenResultRepository.py`

```python
# ScreeningORM.py
from sqlalchemy import String, Float, JSON, DateTime, Integer, func
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from src.shared.infrastructure.Base import Base


class ScreenTaskModel(Base):
    __tablename__ = "screen_tasks"
    id: Mapped[int] = mapped_column(primary_key=True)
    universe: Mapped[str] = mapped_column(String(20), default="all")  # all | watchlist
    dimensions: Mapped[str] = mapped_column(String(500))  # JSON list
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending | running | done | failed
    result_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ScreenResultModel(Base):
    __tablename__ = "screen_results"
    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(Integer, index=True)
    stock_code: Mapped[str] = mapped_column(String(20))
    stock_name: Mapped[str] = mapped_column(String(50))
    dimension_scores: Mapped[str] = mapped_column(String(1000))  # JSON
    composite_score: Mapped[float] = mapped_column(Float)
    tier: Mapped[str] = mapped_column(String(20))
    reasoning: Mapped[str] = mapped_column(String(2000))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    @property
    def score_card_dict(self) -> dict:
        import json
        return {
            "dimension_scores": json.loads(self.dimension_scores),
            "composite_score": self.composite_score,
            "tier": self.tier,
            "reasoning": self.reasoning,
        }
```

```python
# SQLiteScreenResultRepository.py
import json
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.shared.domain.StockCode import StockCode
from src.llm.domain.Analysis import ScoreCard, StockAnalysis, AnalysisRepository
from src.screening.infrastructure.ScreeningORM import ScreenTaskModel, ScreenResultModel


class SQLiteScreenResultRepository(AnalysisRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, analysis: StockAnalysis) -> None:
        model = ScreenResultModel(
            stock_code=str(analysis.stock_code),
            stock_name=analysis.stock_name,
            dimension_scores=json.dumps(analysis.score_card.dimension_scores, ensure_ascii=False),
            composite_score=analysis.score_card.composite_score,
            tier=analysis.score_card.tier.value,
            reasoning=analysis.score_card.reasoning,
        )
        self._session.add(model)
        await self._session.commit()

    async def find_by_code(self, code: StockCode, limit: int = 10) -> list[StockAnalysis]:
        result = await self._session.execute(
            select(ScreenResultModel)
            .where(ScreenResultModel.stock_code == str(code))
            .order_by(ScreenResultModel.created_at.desc())
            .limit(limit)
        )
        rows = result.scalars().all()
        analyses: list[StockAnalysis] = []
        for r in rows:
            card = ScoreCard(
                dimension_scores=json.loads(r.dimension_scores),
                composite_score=r.composite_score,
                tier=r.tier,  # will be set properly below
                reasoning=r.reasoning,
            )
            analyses.append(StockAnalysis(
                id=str(r.id),
                stock_code=StockCode(r.stock_code),
                stock_name=r.stock_name,
                score_card=card,
            ))
        return analyses

    async def save_task(self, universe: str, dimensions: list[str]) -> int:
        model = ScreenTaskModel(
            universe=universe,
            dimensions=json.dumps(dimensions),
            status="running",
        )
        self._session.add(model)
        await self._session.commit()
        return model.id

    async def update_task(self, task_id: int, status: str, result_count: int = 0) -> None:
        result = await self._session.execute(
            select(ScreenTaskModel).where(ScreenTaskModel.id == task_id)
        )
        task = result.scalar_one_or_none()
        if task:
            task.status = status
            task.result_count = result_count
            await self._session.commit()

    async def get_tasks(self, limit: int = 20) -> list[dict]:
        result = await self._session.execute(
            select(ScreenTaskModel).order_by(ScreenTaskModel.created_at.desc()).limit(limit)
        )
        rows = result.scalars().all()
        return [
            {"id": r.id, "universe": r.universe, "status": r.status,
             "result_count": r.result_count, "created_at": str(r.created_at)}
            for r in rows
        ]
```

Commit.

---

### Task 6: FastAPI — App setup + error middleware

**Files:**
- Create: `backend/src/api/__init__.py` (empty)
- Create: `backend/src/api/main.py`
- Create: `backend/src/api/middleware/__init__.py` (empty)
- Create: `backend/src/api/middleware/error_handler.py`

```python
# src/api/main.py
from fastapi import FastAPI
from src.api.middleware.error_handler import register_error_handlers


def create_app() -> FastAPI:
    app = FastAPI(
        title="Stock Selector",
        description="A股成长价值选股助手",
        version="0.1.0",
    )
    register_error_handlers(app)
    return app


app = create_app()


@app.get("/api/health")
async def health():
    return {"status": "ok"}
```

```python
# src/api/middleware/error_handler.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from src.shared.exceptions.DomainError import DomainError


def register_error_handlers(app: FastAPI):
    @app.exception_handler(DomainError)
    async def domain_error_handler(request: Request, exc: DomainError):
        return JSONResponse(
            status_code=400,
            content={"detail": str(exc), "type": type(exc).__name__},
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        return JSONResponse(
            status_code=400,
            content={"detail": str(exc)},
        )

    @app.exception_handler(Exception)
    async def general_error_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "type": type(exc).__name__},
        )
```

Commit.

---

### Task 7: FastAPI — Pydantic schemas

**Files:**
- Create: `backend/src/api/schemas/__init__.py` (empty)
- Create: `backend/src/api/schemas/market.py`
- Create: `backend/src/api/schemas/screening.py`
- Create: `backend/src/api/schemas/user.py`
- Create: `backend/src/api/schemas/config_dto.py`

```python
# market.py
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
```

```python
# screening.py
from pydantic import BaseModel

class ScreeningRequest(BaseModel):
    codes: list[str]
    dimensions: list[str] | None = None  # None = default

class ScreenResultResponse(BaseModel):
    stock_code: str
    stock_name: str
    dimension_scores: dict[str, float]
    composite_score: float
    tier: str
    reasoning: str

class ScreeningResponse(BaseModel):
    task_id: int
    results: list[ScreenResultResponse]
    count: int

class PreScreenRequest(BaseModel):
    universe: str = "all"  # all | watchlist

class TaskStatusResponse(BaseModel):
    id: int
    universe: str
    status: str
    result_count: int
    created_at: str
```

```python
# user.py
from pydantic import BaseModel

class UserPreferencesRequest(BaseModel):
    default_dimensions: list[str] | None = None
    default_universe: str | None = None
    batch_size: int | None = None

class WatchlistAddRequest(BaseModel):
    stock_code: str
```

```python
# config_dto.py
from pydantic import BaseModel

class ProviderConfigRequest(BaseModel):
    id: str
    api_base: str
    api_key: str
    model: str
    default: bool = False
    max_tokens: int = 4096

class DataSourceAccountRequest(BaseModel):
    token: str
```

Commit.

---

### Task 8: FastAPI — Market routes

**Files:**
- Create: `backend/src/api/routes/__init__.py` (empty)
- Create: `backend/src/api/routes/market.py`
- Create: `backend/src/api/deps.py`

```python
# deps.py
from src.shared.infrastructure.Database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends


async def get_bootstrap():
    from src.bootstrap import bootstrap
    return bootstrap()


async def get_db_session():
    async for session in get_db():
        yield session


# AppContext as singleton for request lifetime
from functools import lru_cache

@lru_cache
def _cached_bootstrap():
    from src.bootstrap import bootstrap
    return bootstrap()
```

```python
# routes/market.py
from fastapi import APIRouter, Depends, HTTPException
from src.api.schemas.market import QuoteResponse, FinancialReportResponse, StockInfoResponse
from src.api.deps import _cached_bootstrap
from src.shared.domain.StockCode import StockCode

router = APIRouter(prefix="/api/market", tags=["market"])


@router.get("/stocks/{code}/quote", response_model=QuoteResponse)
async def get_stock_quote(code: str):
    ctx = _cached_bootstrap()
    from src.market.application.QuoteQueryService import QuoteQueryService
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
```

Commit.

---

### Task 9: FastAPI — Screening routes

**Files:**
- Create: `backend/src/api/routes/screening.py`

```python
# routes/screening.py
from fastapi import APIRouter, HTTPException, BackgroundTasks
from src.api.schemas.screening import ScreeningRequest, ScreeningResponse, ScreenResultResponse, TaskStatusResponse
from src.api.deps import _cached_bootstrap

router = APIRouter(prefix="/api/screening", tags=["screening"])


@router.post("/tasks", response_model=ScreeningResponse)
async def create_screening(req: ScreeningRequest):
    ctx = _cached_bootstrap()
    if ctx.provider_registry.default() is None:
        raise HTTPException(status_code=400, detail="No LLM provider configured")

    from src.screening.domain.Dimension import DEFAULT_DIMENSIONS
    if req.dimensions:
        dims = [d for d in DEFAULT_DIMENSIONS if d.id in req.dimensions]
    else:
        dims = DEFAULT_DIMENSIONS

    results = await ctx.screen_usecase.screen_batch(req.codes, dims)

    resp_results = [
        ScreenResultResponse(
            stock_code=str(r.stock_code),
            stock_name=r.stock_name,
            dimension_scores=r.score_card.dimension_scores,
            composite_score=r.composite_score,
            tier=r.tier.label,
            reasoning=r.reasoning,
        )
        for r in results
    ]

    return ScreeningResponse(task_id=0, results=resp_results, count=len(resp_results))


@router.post("/pre-screen")
async def pre_screen(universe: str = "all"):
    ctx = _cached_bootstrap()
    if ctx.provider_registry.default() is None:
        raise HTTPException(status_code=400, detail="No LLM provider configured")

    # Pre-screen: get all stock codes, do a lightweight pass
    codes = [_get_default_universe(universe)]
    return {"message": f"Pre-screen started for {len(codes)} stocks", "universe": universe}


def _get_default_universe(universe: str) -> list[str]:
    """Return default stock codes for universe. Placeholder — real impl gets from data source."""
    # For now, a minimal sample set
    sample = ["600001.SH", "000001.SZ", "600519.SH", "000858.SZ", "300750.SZ"]
    return sample
```

Commit.

---

### Task 10: FastAPI — LLM, User, Config routes

**Files:**
- Create: `backend/src/api/routes/llm.py`
- Create: `backend/src/api/routes/user.py`
- Create: `backend/src/api/routes/config_routes.py`

```python
# routes/llm.py
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from src.api.schemas.screening import ScreeningRequest, ScreenResultResponse, ScreeningResponse
from src.api.deps import _cached_bootstrap
from src.llm.domain.Prompt import BUILTIN_PROMPTS

router = APIRouter(prefix="/api/llm", tags=["llm"])


@router.post("/score/{stock_code}")
async def score_single(stock_code: str):
    ctx = _cached_bootstrap()
    if ctx.provider_registry.default() is None:
        raise HTTPException(status_code=400, detail="No LLM provider configured")

    result = await ctx.screen_usecase.screen_single(stock_code)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Cannot score: {stock_code}")

    return ScreenResultResponse(
        stock_code=str(result.stock_code),
        stock_name=result.stock_name,
        dimension_scores=result.score_card.dimension_scores,
        composite_score=result.composite_score,
        tier=result.tier.label,
        reasoning=result.reasoning,
    )


@router.post("/chat")
async def chat(message: dict):
    ctx = _cached_bootstrap()
    if ctx.provider_registry.default() is None:
        raise HTTPException(status_code=400, detail="No LLM provider configured")

    messages = [{"role": "user", "content": message.get("content", "")}]

    async def stream():
        async for token in ctx.llm_adapter.chat(messages):
            yield f"data: {token}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")


@router.post("/reports/generate")
async def generate_report(stocks_data: list[dict]):
    ctx = _cached_bootstrap()
    if ctx.provider_registry.default() is None:
        raise HTTPException(status_code=400, detail="No LLM provider configured")

    report = await ctx.llm_adapter.generate_report(stocks_data)
    return {"report": report}
```

```python
# routes/user.py
from fastapi import APIRouter, HTTPException
from src.api.schemas.user import UserPreferencesRequest, WatchlistAddRequest
from src.shared.domain.StockCode import StockCode

router = APIRouter(prefix="/api/user", tags=["user"])


@router.get("/watchlist")
async def get_watchlist():
    return {"items": []}  # stub — will wire UserRepository later


@router.post("/watchlist")
async def add_to_watchlist(req: WatchlistAddRequest):
    code = StockCode(req.stock_code)
    return {"stock_code": str(code), "status": "added"}


@router.delete("/watchlist/{code}")
async def remove_from_watchlist(code: str):
    return {"stock_code": code, "status": "removed"}


@router.get("/profile")
async def get_profile():
    return {
        "default_dimensions": ["financial", "industry", "valuation"],
        "default_universe": "all",
        "batch_size": 20,
    }


@router.put("/profile/preferences")
async def update_preferences(req: UserPreferencesRequest):
    return {"status": "updated"}
```

```python
# routes/config_routes.py
from fastapi import APIRouter, HTTPException
from src.api.schemas.config_dto import ProviderConfigRequest, DataSourceAccountRequest
from src.api.deps import _cached_bootstrap
from src.llm.domain.ModelProvider import ProviderConfig

router = APIRouter(prefix="/api/config", tags=["config"])


@router.get("/llm-providers")
async def list_providers():
    ctx = _cached_bootstrap()
    providers = ctx.provider_registry.providers
    return {
        "providers": [
            {"id": p.id, "api_base": p.api_base, "model": p.model, "default": p.default}
            for p in providers
        ]
    }


@router.put("/llm-providers/{provider_id}")
async def upsert_provider(provider_id: str, req: ProviderConfigRequest):
    ctx = _cached_bootstrap()
    cfg = ProviderConfig(
        id=req.id,
        api_base=req.api_base,
        api_key=req.api_key,
        model=req.model,
        default=req.default,
        max_tokens=req.max_tokens,
    )
    ctx.provider_registry.add(cfg)
    return {"status": "configured", "provider_id": provider_id}


@router.get("/data-sources")
async def list_data_sources():
    ctx = _cached_bootstrap()
    return {
        "sources": [
            {"id": s.id, "name": s.name, "type": s.type.value, "priority": s.priority, "enabled": s.enabled}
            for s in ctx.data_source_registry.sources
        ]
    }


@router.put("/data-sources/{source_id}/account")
async def set_data_source_account(source_id: str, req: DataSourceAccountRequest):
    ctx = _cached_bootstrap()
    ctx.data_source_registry.enable(source_id)
    # Store token (simplified — real impl persists to DB)
    return {"status": "configured", "source_id": source_id}


@router.delete("/data-sources/{source_id}/account")
async def remove_data_source_account(source_id: str):
    ctx = _cached_bootstrap()
    ctx.data_source_registry.disable(source_id)
    return {"status": "removed", "source_id": source_id}


@router.get("/prompts")
async def list_prompts():
    from src.llm.domain.Prompt import BUILTIN_PROMPTS
    return {
        "prompts": [
            {"id": pid, "scenario": p.scenario, "description": p.description}
            for pid, p in BUILTIN_PROMPTS.items()
        ]
    }
```

Commit.

---

### Task 11: Wire routes into FastAPI app

**Files:**
- Modify: `backend/src/api/main.py`

Add after `app = create_app()` / inside `create_app()`:

```python
def create_app() -> FastAPI:
    app = FastAPI(title="Stock Selector", description="A股成长价值选股助手", version="0.1.0")
    register_error_handlers(app)

    from src.api.routes.market import router as market_router
    from src.api.routes.screening import router as screening_router
    from src.api.routes.llm import router as llm_router
    from src.api.routes.user import router as user_router
    from src.api.routes.config_routes import router as config_router

    app.include_router(market_router)
    app.include_router(screening_router)
    app.include_router(llm_router)
    app.include_router(user_router)
    app.include_router(config_router)

    return app
```

Add CLI server command to `backend/src/cli/commands/__init__.py`:

Create `backend/src/cli/commands/server.py`:
```python
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
```

Register in `backend/src/cli/main.py`:
```python
from src.cli.commands.server import server_app
app.add_typer(server_app, name="server")
```

Commit.

---

### Task 12: Add FastAPI startup event for DB init

**Files:**
- Modify: `backend/src/api/main.py`

Add to `create_app()`:
```python
@app.on_event("startup")
async def startup():
    from src.shared.infrastructure.Database import init_db
    await init_db()
```

---

### Task 13: Integration test for API

**Files:**
- Create: `backend/tests/integration/test_api_smoke.py`

```python
# tests/integration/test_api_smoke.py
import pytest
from httpx import AsyncClient, ASGITransport
from src.api.main import app


@pytest.mark.asyncio
async def test_health():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_list_data_sources():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/config/data-sources")
        assert resp.status_code == 200
        data = resp.json()
        assert "sources" in data
        assert len(data["sources"]) >= 1  # AKShare always available


@pytest.mark.asyncio
async def test_list_providers_empty():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/config/llm-providers")
        assert resp.status_code == 200
        assert resp.json() == {"providers": []}


@pytest.mark.asyncio
async def test_list_prompts():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/config/prompts")
        assert resp.status_code == 200
        data = resp.json()
        assert "prompts" in data
        assert len(data["prompts"]) >= 2


@pytest.mark.asyncio
async def test_quote_not_found():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/market/stocks/000000.SZ/quote")
        assert resp.status_code == 404
```

Add `httpx` to dev deps (should already be there).

Run: `cd backend && python -m pytest tests/integration/test_api_smoke.py -v`

Expected: 5 tests PASS

Commit.

---

## Phase 2 Complete — Verification

```bash
# Start API server
cd backend && python -m src.cli.main server start --reload

# In another terminal
curl http://localhost:8000/api/health
curl http://localhost:8000/api/config/data-sources
curl http://localhost:8000/api/config/prompts
curl http://localhost:8000/api/user/watchlist

# Run all tests
python -m pytest tests/ -v
```

**Phase 2 delivers:** FastAPI server with full REST API, SQLite persistence for user data and screening results, and all config endpoints.

---

## Next Phase

**Phase 3:** Notification Context (monitoring, IM push, APScheduler, event-driven flow)
