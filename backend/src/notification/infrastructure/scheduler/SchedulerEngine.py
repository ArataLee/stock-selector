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
        try:
            codes = await self._get_universe_codes(task.universe_type)
            dims = [d for d in DEFAULT_DIMENSIONS if d.id in task.dimensions] if task.dimensions else DEFAULT_DIMENSIONS
            outcome = await self._screen_usecase.screen_batch(codes, dims)

            if not outcome.results:
                return

            stocks_data = [
                {"code": str(r.stock_code), "name": r.stock_name,
                 "score": r.composite_score, "tier": r.tier.label, "reasoning": r.reasoning}
                for r in outcome.results[:10]
            ]
            report = await self._llm_adapter.generate_report(stocks_data)

            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            message = PushMessage(
                title=f"📈 A股成长股扫描报告 — {now}",
                stock_list=stocks_data, summary=report, generated_at=now,
            )

            channels = await self._channel_repo.list_enabled(task.user_id)
            for ch in channels:
                if not task.channels or ch.id in task.channels:
                    adapter = create_channel_adapter(ch)
                    try:
                        await adapter.send(message)
                    finally:
                        await adapter.close()

            await self._monitor_repo.update_status(task.id, MonitorStatus.ACTIVE)
        except Exception:
            pass

    async def _get_universe_codes(self, universe: str) -> list[str]:
        if universe == "watchlist":
            return []
        return ["600001.SH", "600519.SH", "000001.SZ", "000858.SZ",
                "300750.SZ", "600036.SH", "601318.SH", "000333.SZ"]
