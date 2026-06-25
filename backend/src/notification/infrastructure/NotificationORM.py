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
