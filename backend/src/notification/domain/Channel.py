from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class ChannelType(str, Enum):
    WECOM = "wecom"
    FEISHU = "feishu"
    DINGTALK = "dingtalk"


@dataclass
class ChannelConfig:
    id: str | None
    type: ChannelType
    webhook_url: str
    user_id: str = "default"
    name: str = ""
    enabled: bool = True


class ChannelRepository(ABC):
    @abstractmethod
    async def save(self, channel: ChannelConfig) -> str: ...
    @abstractmethod
    async def list_enabled(self, user_id: str = "default") -> list[ChannelConfig]: ...
    @abstractmethod
    async def delete(self, channel_id: str) -> None: ...
