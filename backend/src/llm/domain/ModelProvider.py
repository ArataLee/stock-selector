from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class ProviderConfig:
    id: str
    api_base: str
    api_key: str
    model: str
    default: bool = False
    max_tokens: int = 4096
    temperature: float = 0.7


@dataclass
class ProviderRegistry:
    providers: list[ProviderConfig] = field(default_factory=list)

    def default(self) -> ProviderConfig | None:
        for p in self.providers:
            if p.default:
                return p
        return self.providers[0] if self.providers else None

    def find(self, provider_id: str) -> ProviderConfig | None:
        for p in self.providers:
            if p.id == provider_id:
                return p
        return None

    def add(self, cfg: ProviderConfig) -> None:
        existing = self.find(cfg.id)
        if existing:
            self.providers.remove(existing)
        self.providers.append(cfg)

    def remove(self, provider_id: str) -> None:
        self.providers = [p for p in self.providers if p.id != provider_id]
