import json
import httpx
from src.llm.domain.ModelProvider import ProviderConfig


class LLMClient:
    def __init__(self, provider: ProviderConfig, timeout: float = 60.0) -> None:
        self._provider = provider
        self._client = httpx.AsyncClient(
            base_url=provider.api_base.rstrip("/"),
            headers={
                "Authorization": f"Bearer {provider.api_key}",
                "Content-Type": "application/json",
            },
            timeout=timeout,
        )

    async def chat(
        self,
        messages: list[dict],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        temp = temperature if temperature is not None else self._provider.temperature
        max_tok = max_tokens if max_tokens is not None else self._provider.max_tokens

        response = await self._client.post(
            "/chat/completions",
            json={
                "model": self._provider.model,
                "messages": messages,
                "temperature": temp,
                "max_tokens": max_tok,
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

    async def chat_stream(
        self,
        messages: list[dict],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ):
        temp = temperature if temperature is not None else self._provider.temperature
        max_tok = max_tokens if max_tokens is not None else self._provider.max_tokens

        async with self._client.stream(
            "POST",
            "/chat/completions",
            json={
                "model": self._provider.model,
                "messages": messages,
                "temperature": temp,
                "max_tokens": max_tok,
                "stream": True,
            },
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break
                    chunk = json.loads(data_str)
                    delta = chunk["choices"][0].get("delta", {})
                    if "content" in delta:
                        yield delta["content"]

    async def close(self) -> None:
        await self._client.aclose()
