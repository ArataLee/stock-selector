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
    cron_expr: str = "0 18 * * 1-5"
    universe_type: str = "all"
    dimensions: list[str] = field(default_factory=lambda: ["financial", "industry", "valuation"])
    channels: list[str] = field(default_factory=list)
    status: MonitorStatus = MonitorStatus.DISABLED
    last_run_at: str | None = None


class MonitorRepository(ABC):
    @abstractmethod
    async def save(self, task: MonitorTask) -> str: ...
    @abstractmethod
    async def get(self, task_id: str) -> MonitorTask | None: ...
    @abstractmethod
    async def list_active(self) -> list[MonitorTask]: ...
    @abstractmethod
    async def update_status(self, task_id: str, status: MonitorStatus) -> None: ...
    @abstractmethod
    async def delete(self, task_id: str) -> None: ...
