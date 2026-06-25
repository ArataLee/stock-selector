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
            result = await self._session.execute(select(MonitorTaskModel).where(MonitorTaskModel.id == int(task.id)))
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
        result = await self._session.execute(select(MonitorTaskModel).where(MonitorTaskModel.id == int(task_id)))
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def list_active(self) -> list[MonitorTask]:
        result = await self._session.execute(select(MonitorTaskModel).where(MonitorTaskModel.status == MonitorStatus.ACTIVE.value))
        return [self._to_domain(m) for m in result.scalars().all()]

    async def update_status(self, task_id: str, status: MonitorStatus) -> None:
        await self._session.execute(update(MonitorTaskModel).where(MonitorTaskModel.id == int(task_id)).values(status=status.value, last_run_at=datetime.now()))
        await self._session.commit()

    async def delete(self, task_id: str) -> None:
        result = await self._session.execute(select(MonitorTaskModel).where(MonitorTaskModel.id == int(task_id)))
        model = result.scalar_one_or_none()
        if model:
            await self._session.delete(model)
            await self._session.commit()

    @staticmethod
    def _to_domain(model: MonitorTaskModel) -> MonitorTask:
        return MonitorTask(
            id=str(model.id), user_id=model.user_id, name=model.name,
            cron_expr=model.cron_expr, universe_type=model.universe_type,
            dimensions=json.loads(model.dimensions) if isinstance(model.dimensions, str) else model.dimensions,
            channels=json.loads(model.channels) if isinstance(model.channels, str) else model.channels,
            status=MonitorStatus(model.status),
            last_run_at=str(model.last_run_at) if model.last_run_at else None,
        )
