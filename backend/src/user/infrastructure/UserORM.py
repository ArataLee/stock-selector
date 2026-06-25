from sqlalchemy import String, DateTime, func
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
