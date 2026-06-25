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
            payload = {"msgtype": "markdown", "markdown": {"title": message.title, "text": content}}
            resp = await self._client.post(self._config.webhook_url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data.get("errcode") == 0
        except Exception:
            return False

    async def close(self):
        await self._client.aclose()
