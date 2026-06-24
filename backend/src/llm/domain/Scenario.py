from dataclasses import dataclass
from enum import Enum


class ScenarioType(Enum):
    CONVERSATION = "conversation"
    SCORING = "scoring"
    REPORT = "report"


@dataclass(frozen=True)
class ScenarioConfig:
    scenario: ScenarioType
    provider_id: str
    provider_override: str | None = None
