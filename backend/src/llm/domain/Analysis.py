from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from src.shared.domain.StockCode import StockCode
from src.shared.domain.ScoreTier import ScoreTier, tier_from_score


@dataclass
class ScoreCard:
    dimension_scores: dict[str, float]
    composite_score: float
    tier: ScoreTier
    reasoning: str

    @staticmethod
    def from_llm_output(data: dict) -> ScoreCard:
        composite = float(data["composite_score"])
        return ScoreCard(
            dimension_scores={k: float(v) for k, v in data["dimension_scores"].items()},
            composite_score=composite,
            tier=tier_from_score(composite),
            reasoning=str(data["reasoning"]),
        )


@dataclass
class StockAnalysis:
    id: str | None
    stock_code: StockCode
    stock_name: str
    score_card: ScoreCard
    created_at: datetime = field(default_factory=datetime.now)


class AnalysisRepository(ABC):
    @abstractmethod
    async def save(self, analysis: StockAnalysis) -> None:
        ...

    @abstractmethod
    async def find_by_code(self, code: StockCode, limit: int = 10) -> list[StockAnalysis]:
        ...
