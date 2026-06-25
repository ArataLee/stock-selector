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
        await self._session.execute(delete(UserPreferencesModel))
        row = UserPreferencesModel(
            default_dimensions=json.dumps(prefs.default_dimensions),
            default_universe=prefs.default_universe,
            batch_size=prefs.batch_size,
        )
        self._session.add(row)
        await self._session.commit()

    async def get_watchlist(self) -> list[WatchlistItem]:
        result = await self._session.execute(
            select(WatchlistModel).order_by(WatchlistModel.added_at.desc())
        )
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
