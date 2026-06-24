from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum


class DataSourceType(Enum):
    FREE = "free"
    ACCOUNT = "account"


@dataclass(frozen=True)
class DataSourceId:
    id: str
    name: str
    type: DataSourceType
    priority: int
    enabled: bool

    @staticmethod
    def from_config(cfg: dict) -> DataSourceId:
        return DataSourceId(
            id=cfg["id"],
            name=cfg["name"],
            type=DataSourceType(cfg["type"]),
            priority=cfg["priority"],
            enabled=cfg.get("enabled", True),
        )


@dataclass
class DataSourceRegistry:
    sources: list[DataSourceId] = field(default_factory=list)

    def enabled_sources(self) -> list[DataSourceId]:
        return sorted(
            [s for s in self.sources if s.enabled],
            key=lambda s: s.priority,
        )

    def find(self, source_id: str) -> DataSourceId | None:
        for s in self.sources:
            if s.id == source_id:
                return s
        return None

    def enable(self, source_id: str) -> None:
        s = self.find(source_id)
        if s is None:
            raise ValueError(f"Unknown data source: {source_id}")
        self.sources = [
            DataSourceId(s.id, s.name, s.type, s.priority, True) if item.id == source_id else item
            for item in self.sources
        ]

    def disable(self, source_id: str) -> None:
        s = self.find(source_id)
        if s is None:
            raise ValueError(f"Unknown data source: {source_id}")
        self.sources = [
            DataSourceId(s.id, s.name, s.type, s.priority, False) if item.id == source_id else item
            for item in self.sources
        ]

    @staticmethod
    def from_config_list(configs: list[dict]) -> DataSourceRegistry:
        return DataSourceRegistry(
            sources=[DataSourceId.from_config(c) for c in configs]
        )
