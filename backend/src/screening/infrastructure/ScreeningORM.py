from sqlalchemy import String, Float, JSON, DateTime, Integer, func
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from src.shared.infrastructure.Base import Base


class ScreenTaskModel(Base):
    __tablename__ = "screen_tasks"
    id: Mapped[int] = mapped_column(primary_key=True)
    universe: Mapped[str] = mapped_column(String(20), default="all")
    dimensions: Mapped[str] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    result_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ScreenResultModel(Base):
    __tablename__ = "screen_results"
    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(Integer, index=True)
    stock_code: Mapped[str] = mapped_column(String(20))
    stock_name: Mapped[str] = mapped_column(String(50))
    dimension_scores: Mapped[str] = mapped_column(String(1000))
    composite_score: Mapped[float] = mapped_column(Float)
    tier: Mapped[str] = mapped_column(String(20))
    reasoning: Mapped[str] = mapped_column(String(2000))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
