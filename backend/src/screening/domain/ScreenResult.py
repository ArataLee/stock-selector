from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from src.shared.domain.StockCode import StockCode
from src.shared.domain.ScoreTier import ScoreTier
from src.llm.domain.Analysis import ScoreCard


@dataclass
class ScreenResult:
    stock_code: StockCode
    stock_name: str
    score_card: ScoreCard
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def composite_score(self) -> float:
        return self.score_card.composite_score

    @property
    def tier(self) -> ScoreTier:
        return self.score_card.tier

    @property
    def reasoning(self) -> str:
        return self.score_card.reasoning
