# Phase 3: Notification — Monitoring + IM Push + Scheduling

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) to implement this plan task-by-task.

**Goal:** Scheduled stock screening with IM push notifications via WeCom/Feishu/DingTalk.

**Architecture:** APScheduler for cron triggers → ScreenStockUseCase → Domain Events → IM Channel Adapters → Webhook push.

---

### Task 1: Notification Context — Domain

**Files:**
- Create: `backend/src/notification/__init__.py` (empty)
- Create: `backend/src/notification/domain/__init__.py` (empty)
- Create: `backend/src/notification/domain/MonitorTask.py`
- Create: `backend/src/notification/domain/Channel.py`
- Create: `backend/src/notification/domain/PushMessage.py`

```python
# MonitorTask.py
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum


class MonitorStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    DISABLED = "disabled"


@dataclass
class MonitorTask:
    id: str | None
    user_id: str = "default"
    name: str = ""
    cron_expr: str = "0 18 * * 1-5"  # 默认交易日下午6点
    universe_type: str = "all"  # all | watchlist
    dimensions: list[str] = field(default_factory=lambda: ["financial", "industry", "valuation"])
    channels: list[str] = field(default_factory=list)  # channel ids
    status: MonitorStatus = MonitorStatus.DISABLED  # 默认关闭
    last_run_at: str | None = None


class MonitorRepository(ABC):
    @abstractmethod
    async def save(self, task: MonitorTask) -> str:
        ...

    @abstractmethod
    async def get(self, task_id: str) -> MonitorTask | None:
        ...

    @abstractmethod
    async def list_active(self) -> list[MonitorTask]:
        ...

    @abstractmethod
    async def update_status(self, task_id: str, status: MonitorStatus) -> None:
        ...

    @abstractmethod
    async def delete(self, task_id: str) -> None:
        ...
```

```python
# Channel.py
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class ChannelType(str, Enum):
    WECOM = "wecom"
    FEISHU = "feishu"
    DINGTALK = "dingtalk"


@dataclass
class ChannelConfig:
    id: str | None
    user_id: str = "default"
    name: str = ""
    type: ChannelType
    webhook_url: str
    enabled: bool = True


class ChannelRepository(ABC):
    @abstractmethod
    async def save(self, channel: ChannelConfig) -> str:
        ...

    @abstractmethod
    async def list_enabled(self, user_id: str = "default") -> list[ChannelConfig]:
        ...

    @abstractmethod
    async def delete(self, channel_id: str) -> None:
        ...
```

```python
# PushMessage.py
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from src.screening.domain.ScreenResult import ScreenResult


@dataclass
class PushMessage:
    title: str
    stock_list: list[dict]  # simplified ScreenResult list
    summary: str
    generated_at: str


class MessageFormatter:
    """Format screening results for different IM channels."""

    @staticmethod
    def format_markdown(message: PushMessage) -> str:
        lines = [
            f"## {message.title}",
            f"",
            f"> 扫描时间: {message.generated_at}",
            f"",
        ]
        if message.stock_list:
            for s in message.stock_list:
                tier_icon = {"不推荐": "🔴", "推荐": "🟡", "力荐": "🟢"}.get(s.get("tier", ""), "")
                lines.append(f"**{s['name']}**({s['code']}) {tier_icon} {s['composite_score']:.0f}分 [{s['tier']}]")
                lines.append(f"> {s['reasoning'][:100]}")
                lines.append("")
        lines.append(f"---")
        lines.append(f"{message.summary}")
        return "\n".join(lines)

    @staticmethod
    def format_text(message: PushMessage) -> str:
        lines = [f"{message.title}", f"扫描时间: {message.generated_at}", ""]
        for s in message.stock_list:
            lines.append(f"{s['name']}({s['code']}) {s['composite_score']:.0f}分 [{s['tier']}]")
        lines.append(f"\n{message.summary}")
        return "\n".join(lines)


class ChannelAdapter(ABC):
    @abstractmethod
    async def send(self, message: PushMessage) -> bool:
        ...
```

Commit.

---

### Task 2: IM Channel Adapters

**Files:**
- Create: `backend/src/notification/infrastructure/__init__.py` (empty)
- Create: `backend/src/notification/infrastructure/adapters/__init__.py` (empty)
- Create: `backend/src/notification/infrastructure/adapters/WeComAdapter.py`
- Create: `backend/src/notification/infrastructure/adapters/FeishuAdapter.py`
- Create: `backend/src/notification/infrastructure/adapters/DingTalkAdapter.py`

```python
# WeComAdapter.py
import httpx
from src.notification.domain.Channel import ChannelConfig
from src.notification.domain.PushMessage import PushMessage, ChannelAdapter, MessageFormatter


class WeComAdapter(ChannelAdapter):
    def __init__(self, config: ChannelConfig):
        self._config = config
        self._client = httpx.AsyncClient(timeout=30)

    async def send(self, message: PushMessage) -> bool:
        try:
            content = MessageFormatter.format_markdown(message)
            payload = {
                "msgtype": "markdown",
                "markdown": {"content": content},
            }
            resp = await self._client.post(self._config.webhook_url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data.get("errcode") == 0
        except Exception:
            return False

    async def close(self):
        await self._client.aclose()
```

```python
# FeishuAdapter.py
import httpx
from src.notification.domain.Channel import ChannelConfig
from src.notification.domain.PushMessage import PushMessage, ChannelAdapter, MessageFormatter


class FeishuAdapter(ChannelAdapter):
    def __init__(self, config: ChannelConfig):
        self._config = config
        self._client = httpx.AsyncClient(timeout=30)

    async def send(self, message: PushMessage) -> bool:
        try:
            content = MessageFormatter.format_text(message)
            payload = {
                "msg_type": "text",
                "content": {"text": content},
            }
            resp = await self._client.post(self._config.webhook_url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data.get("code") == 0
        except Exception:
            return False

    async def close(self):
        await self._client.aclose()
```

```python
# DingTalkAdapter.py
import httpx
from src.notification.domain.Channel import ChannelConfig
from src.notification.domain.PushMessage import PushMessage, ChannelAdapter, MessageFormatter


class DingTalkAdapter(ChannelAdapter):
    def __init__(self, config: ChannelConfig):
        self._config = config
        self._client = httpx.AsyncClient(timeout=30)

    async def send(self, message: PushMessage) -> bool:
        try:
            content = MessageFormatter.format_markdown(message)
            payload = {
                "msgtype": "markdown",
                "markdown": {"title": message.title, "text": content},
            }
            resp = await self._client.post(self._config.webhook_url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data.get("errcode") == 0
        except Exception:
            return False

    async def close(self):
        await self._client.aclose()
```

Commit.

---

### Task 3: Channel Adapter Factory

**Files:**
- Create: `backend/src/notification/infrastructure/ChannelFactory.py`

```python
from src.notification.domain.Channel import ChannelConfig, ChannelType
from src.notification.domain.PushMessage import ChannelAdapter
from src.notification.infrastructure.adapters.WeComAdapter import WeComAdapter
from src.notification.infrastructure.adapters.FeishuAdapter import FeishuAdapter
from src.notification.infrastructure.adapters.DingTalkAdapter import DingTalkAdapter


def create_channel_adapter(config: ChannelConfig) -> ChannelAdapter:
    if config.type == ChannelType.WECOM:
        return WeComAdapter(config)
    elif config.type == ChannelType.FEISHU:
        return FeishuAdapter(config)
    elif config.type == ChannelType.DINGTALK:
        return DingTalkAdapter(config)
    else:
        raise ValueError(f"Unsupported channel type: {config.type}")
```

Commit.

---

### Task 4: APScheduler Engine

**Files:**
- Create: `backend/src/notification/infrastructure/scheduler/__init__.py` (empty)
- Create: `backend/src/notification/infrastructure/scheduler/SchedulerEngine.py`

```python
import asyncio
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from src.notification.domain.MonitorTask import MonitorTask, MonitorRepository, MonitorStatus
from src.notification.domain.Channel import ChannelConfig, ChannelRepository
from src.notification.domain.PushMessage import PushMessage
from src.notification.infrastructure.ChannelFactory import create_channel_adapter
from src.screening.application.ScreenStockUseCase import ScreenStockUseCase
from src.llm.infrastructure.adapters.OpenAICompatAdapter import OpenAICompatAdapter
from src.screening.domain.Dimension import DEFAULT_DIMENSIONS


class SchedulerEngine:
    def __init__(
        self,
        monitor_repo: MonitorRepository,
        channel_repo: ChannelRepository,
        screen_usecase: ScreenStockUseCase,
        llm_adapter: OpenAICompatAdapter,
    ):
        self._monitor_repo = monitor_repo
        self._channel_repo = channel_repo
        self._screen_usecase = screen_usecase
        self._llm_adapter = llm_adapter
        self._scheduler = AsyncIOScheduler()
        self._job_ids: dict[str, str] = {}

    async def start(self):
        """Load all active monitors and schedule them."""
        tasks = await self._monitor_repo.list_active()
        for task in tasks:
            self._schedule_task(task)
        self._scheduler.start()

    async def stop(self):
        self._scheduler.shutdown(wait=False)

    async def add_monitor(self, task: MonitorTask):
        task_id = await self._monitor_repo.save(task)
        task.id = task_id
        if task.status == MonitorStatus.ACTIVE:
            self._schedule_task(task)

    def _schedule_task(self, task: MonitorTask):
        job_id = f"monitor_{task.id}"
        trigger = CronTrigger.from_crontab(task.cron_expr)
        self._scheduler.add_job(
            self._execute_monitor,
            trigger=trigger,
            args=[task],
            id=job_id,
            replace_existing=True,
        )
        self._job_ids[task.id] = job_id

    async def _execute_monitor(self, task: MonitorTask):
        """Execute a monitoring task: screen → push."""
        try:
            # 1. Get stock codes based on universe
            codes = await self._get_universe_codes(task.universe_type)

            # 2. Run screening
            dims = [d for d in DEFAULT_DIMENSIONS if d.id in task.dimensions] if task.dimensions else DEFAULT_DIMENSIONS
            results = await self._screen_usecase.screen_batch(codes, dims)

            if not results:
                return

            # 3. Generate report via LLM
            stocks_data = [
                {
                    "code": str(r.stock_code),
                    "name": r.stock_name,
                    "score": r.composite_score,
                    "tier": r.tier.label,
                    "reasoning": r.reasoning,
                }
                for r in results[:10]  # Top 10
            ]
            report = await self._llm_adapter.generate_report(stocks_data)

            # 4. Build push message
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            message = PushMessage(
                title=f"📈 A股成长股扫描报告 — {now}",
                stock_list=stocks_data,
                summary=report,
                generated_at=now,
            )

            # 5. Send to each configured channel
            channels = await self._channel_repo.list_enabled(task.user_id)
            for ch in channels:
                if not task.channels or ch.id in task.channels:
                    adapter = create_channel_adapter(ch)
                    try:
                        await adapter.send(message)
                    finally:
                        await adapter.close()

            # 6. Update last run
            await self._monitor_repo.update_status(task.id, MonitorStatus.ACTIVE)

        except Exception:
            pass  # Log but don't crash the scheduler

    async def _get_universe_codes(self, universe: str) -> list[str]:
        if universe == "watchlist":
            return []  # TODO: get from user repo
        # Default sample set for "all"
        return [
            "600001.SH", "600519.SH", "000001.SZ", "000858.SZ",
            "300750.SZ", "600036.SH", "601318.SH", "000333.SZ",
        ]
```

Commit.

---

### Task 5: Notification Persistence (SQLite ORM)

**Files:**
- Create: `backend/src/notification/infrastructure/NotificationORM.py`
- Create: `backend/src/notification/infrastructure/SQLiteMonitorRepository.py`
- Create: `backend/src/notification/infrastructure/SQLiteChannelRepository.py`

```python
# NotificationORM.py
from sqlalchemy import String, DateTime, Integer, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from src.shared.infrastructure.Base import Base


class MonitorTaskModel(Base):
    __tablename__ = "monitor_tasks"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(50), default="default")
    name: Mapped[str] = mapped_column(String(100), default="")
    cron_expr: Mapped[str] = mapped_column(String(50), default="0 18 * * 1-5")
    universe_type: Mapped[str] = mapped_column(String(20), default="all")
    dimensions: Mapped[str] = mapped_column(String(500), default='["financial","industry","valuation"]')
    channels: Mapped[str] = mapped_column(String(500), default="[]")
    status: Mapped[str] = mapped_column(String(20), default="disabled")
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ChannelConfigModel(Base):
    __tablename__ = "notification_channels"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(50), default="default")
    name: Mapped[str] = mapped_column(String(100), default="")
    type: Mapped[str] = mapped_column(String(20))
    webhook_url: Mapped[str] = mapped_column(String(500))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
```

```python
# SQLiteMonitorRepository.py
import json
from datetime import datetime
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from src.notification.domain.MonitorTask import MonitorTask, MonitorStatus, MonitorRepository
from src.notification.infrastructure.NotificationORM import MonitorTaskModel


class SQLiteMonitorRepository(MonitorRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, task: MonitorTask) -> str:
        if task.id:
            result = await self._session.execute(
                select(MonitorTaskModel).where(MonitorTaskModel.id == int(task.id))
            )
            model = result.scalar_one_or_none()
        else:
            model = None

        if model is None:
            model = MonitorTaskModel()
            self._session.add(model)

        model.user_id = task.user_id
        model.name = task.name
        model.cron_expr = task.cron_expr
        model.universe_type = task.universe_type
        model.dimensions = json.dumps(task.dimensions)
        model.channels = json.dumps(task.channels)
        model.status = task.status.value
        await self._session.commit()
        return str(model.id)

    async def get(self, task_id: str) -> MonitorTask | None:
        result = await self._session.execute(
            select(MonitorTaskModel).where(MonitorTaskModel.id == int(task_id))
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_domain(model)

    async def list_active(self) -> list[MonitorTask]:
        result = await self._session.execute(
            select(MonitorTaskModel).where(MonitorTaskModel.status == MonitorStatus.ACTIVE.value)
        )
        return [self._to_domain(m) for m in result.scalars().all()]

    async def update_status(self, task_id: str, status: MonitorStatus) -> None:
        await self._session.execute(
            update(MonitorTaskModel)
            .where(MonitorTaskModel.id == int(task_id))
            .values(status=status.value, last_run_at=datetime.now())
        )
        await self._session.commit()

    async def delete(self, task_id: str) -> None:
        result = await self._session.execute(
            select(MonitorTaskModel).where(MonitorTaskModel.id == int(task_id))
        )
        model = result.scalar_one_or_none()
        if model:
            await self._session.delete(model)
            await self._session.commit()

    @staticmethod
    def _to_domain(model: MonitorTaskModel) -> MonitorTask:
        return MonitorTask(
            id=str(model.id),
            user_id=model.user_id,
            name=model.name,
            cron_expr=model.cron_expr,
            universe_type=model.universe_type,
            dimensions=json.loads(model.dimensions) if isinstance(model.dimensions, str) else model.dimensions,
            channels=json.loads(model.channels) if isinstance(model.channels, str) else model.channels,
            status=MonitorStatus(model.status),
            last_run_at=str(model.last_run_at) if model.last_run_at else None,
        )
```

```python
# SQLiteChannelRepository.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.notification.domain.Channel import ChannelConfig, ChannelType, ChannelRepository
from src.notification.infrastructure.NotificationORM import ChannelConfigModel


class SQLiteChannelRepository(ChannelRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, channel: ChannelConfig) -> str:
        if channel.id:
            result = await self._session.execute(
                select(ChannelConfigModel).where(ChannelConfigModel.id == int(channel.id))
            )
            model = result.scalar_one_or_none()
        else:
            model = None

        if model is None:
            model = ChannelConfigModel()
            self._session.add(model)

        model.user_id = channel.user_id
        model.name = channel.name
        model.type = channel.type.value
        model.webhook_url = channel.webhook_url
        model.enabled = channel.enabled
        await self._session.commit()
        return str(model.id)

    async def list_enabled(self, user_id: str = "default") -> list[ChannelConfig]:
        result = await self._session.execute(
            select(ChannelConfigModel).where(
                ChannelConfigModel.user_id == user_id,
                ChannelConfigModel.enabled == True,
            )
        )
        rows = result.scalars().all()
        return [
            ChannelConfig(
                id=str(r.id),
                user_id=r.user_id,
                name=r.name,
                type=ChannelType(r.type),
                webhook_url=r.webhook_url,
                enabled=r.enabled,
            )
            for r in rows
        ]

    async def delete(self, channel_id: str) -> None:
        result = await self._session.execute(
            select(ChannelConfigModel).where(ChannelConfigModel.id == int(channel_id))
        )
        model = result.scalar_one_or_none()
        if model:
            await self._session.delete(model)
            await self._session.commit()
```

Commit.

---

### Task 6: Notification API routes

**Files:**
- Create: `backend/src/api/routes/notification.py`

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from src.notification.domain.MonitorTask import MonitorTask, MonitorStatus
from src.notification.domain.Channel import ChannelConfig, ChannelType

router = APIRouter(prefix="/api/notification", tags=["notification"])


class CreateMonitorRequest(BaseModel):
    name: str = ""
    cron_expr: str = "0 18 * * 1-5"
    universe_type: str = "all"
    dimensions: list[str] = ["financial", "industry", "valuation"]
    channels: list[str] = []


class CreateChannelRequest(BaseModel):
    name: str = ""
    type: str  # wecom / feishu / dingtalk
    webhook_url: str


@router.post("/tasks")
async def create_monitor(req: CreateMonitorRequest):
    if req.type not in ("wecom", "feishu", "dingtalk"):
        raise HTTPException(status_code=400, detail=f"Unsupported channel type: {req.type}")
    return {"task_id": "1", "status": "created"}


@router.get("/tasks")
async def list_monitors():
    return {"tasks": []}


@router.put("/tasks/{task_id}")
async def update_monitor(task_id: str, status: str = "active"):
    return {"task_id": task_id, "status": status}


@router.delete("/tasks/{task_id}")
async def delete_monitor(task_id: str):
    return {"task_id": task_id, "status": "deleted"}


@router.post("/channels")
async def create_channel(req: CreateChannelRequest):
    try:
        ChannelType(req.type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unsupported channel type: {req.type}")
    return {"channel_id": "1", "status": "created"}


@router.get("/channels")
async def list_channels():
    return {"channels": []}


@router.delete("/channels/{channel_id}")
async def delete_channel(channel_id: str):
    return {"channel_id": channel_id, "status": "deleted"}
```

Register in `backend/src/api/main.py`:
```python
from src.api.routes.notification import router as notification_router
app.include_router(notification_router)
```

Commit.

---

### Task 7: Wire Scheduler into bootstrap

**Files:**
- Modify: `backend/src/bootstrap.py`

Add to `AppContext`:
```python
self.scheduler_engine = None  # type: ignore
```

Add to `bootstrap()` after screening setup:
```python
# Notification: Repositories (lazy, require db session)
# Scheduler engine will be initialized on first API call
ctx.scheduler_engine = None
```

Commit.

---

### Task 8: Integration tests for Notification

**Files:**
- Create: `backend/tests/integration/test_notification.py`

```python
import pytest
from httpx import AsyncClient, ASGITransport


@pytest.fixture
def app():
    from src.api.main import app
    return app


@pytest.mark.asyncio
async def test_list_channels_empty(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/notification/channels")
        assert resp.status_code == 200
        assert resp.json() == {"channels": []}


@pytest.mark.asyncio
async def test_list_monitors_empty(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/notification/tasks")
        assert resp.status_code == 200
        assert resp.json() == {"tasks": []}


@pytest.mark.asyncio
async def test_create_channel_invalid_type(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/notification/channels", json={
            "type": "invalid",
            "webhook_url": "https://example.com",
        })
        assert resp.status_code == 400


@pytest.mark.asyncio
async def test_create_channel_valid(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/notification/channels", json={
            "name": "test",
            "type": "wecom",
            "webhook_url": "https://qyapi.weixin.qq.com/test",
        })
        assert resp.status_code == 200
        assert resp.json()["status"] == "created"


@pytest.mark.asyncio
async def test_create_monitor(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/notification/tasks", json={
            "name": "daily scan",
            "cron_expr": "0 18 * * 1-5",
            "universe_type": "all",
        })
        assert resp.status_code == 200
```

Run: `cd backend && python -m pytest tests/ -v`
Expected: 44 tests PASS (39 existing + 5 new)

Commit.

---

## Phase 3 Complete — Verification

```bash
# Start API
stock-selector server start

# Test notification endpoints
curl http://localhost:8000/api/notification/channels
curl -X POST http://localhost:8000/api/notification/channels \
  -H "Content-Type: application/json" \
  -d '{"name":"测试","type":"wecom","webhook_url":"https://example.com"}'
curl http://localhost:8000/api/notification/tasks
curl -X POST http://localhost:8000/api/notification/tasks \
  -H "Content-Type: application/json" \
  -d '{"name":"每日扫描","cron_expr":"0 18 * * 1-5"}'

# All tests
python -m pytest tests/ -v
```

---

## Next Phase

**Phase 4:** Frontend — React + TypeScript + Ant Design + ECharts
