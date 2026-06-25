from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.notification.domain.Channel import ChannelConfig, ChannelType, ChannelRepository
from src.notification.infrastructure.NotificationORM import ChannelConfigModel


class SQLiteChannelRepository(ChannelRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, channel: ChannelConfig) -> str:
        if channel.id:
            result = await self._session.execute(select(ChannelConfigModel).where(ChannelConfigModel.id == int(channel.id)))
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
        result = await self._session.execute(select(ChannelConfigModel).where(ChannelConfigModel.user_id == user_id, ChannelConfigModel.enabled == True))
        return [ChannelConfig(id=str(r.id), user_id=r.user_id, name=r.name, type=ChannelType(r.type), webhook_url=r.webhook_url, enabled=r.enabled) for r in result.scalars().all()]

    async def delete(self, channel_id: str) -> None:
        result = await self._session.execute(select(ChannelConfigModel).where(ChannelConfigModel.id == int(channel_id)))
        model = result.scalar_one_or_none()
        if model:
            await self._session.delete(model)
            await self._session.commit()
