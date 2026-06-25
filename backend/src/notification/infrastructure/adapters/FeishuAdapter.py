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
            payload = {"msg_type": "text", "content": {"text": content}}
            resp = await self._client.post(self._config.webhook_url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data.get("code") == 0
        except Exception:
            return False

    async def close(self):
        await self._client.aclose()
