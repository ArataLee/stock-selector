from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class PushMessage:
    title: str
    stock_list: list[dict]
    summary: str
    generated_at: str


class MessageFormatter:
    @staticmethod
    def format_markdown(message: PushMessage) -> str:
        lines = [f"## {message.title}", f"", f"> 扫描时间: {message.generated_at}", f""]
        for s in message.stock_list:
            tier_icon = {"不推荐": "🔴", "推荐": "🟡", "力荐": "🟢"}.get(s.get("tier", ""), "")
            lines.append(f"**{s['name']}**({s['code']}) {tier_icon} {s['composite_score']:.0f}分 [{s['tier']}]")
            lines.append(f"> {s['reasoning'][:100]}")
            lines.append("")
        lines.append(f"---")
        lines.append(f"{message.summary}")
        return "\n".join(lines)

    @staticmethod
    def format_text(message: PushMessage) -> str:
        lines = [f"{message.title}", f"扫描时间: {message.generated_at}", ""]
        for s in message.stock_list:
            lines.append(f"{s['name']}({s['code']}) {s['composite_score']:.0f}分 [{s['tier']}]")
        lines.append(f"\n{message.summary}")
        return "\n".join(lines)


class ChannelAdapter(ABC):
    @abstractmethod
    async def send(self, message: PushMessage) -> bool: ...
