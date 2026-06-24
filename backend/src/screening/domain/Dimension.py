from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Dimension:
    id: str
    name: str
    description: str
    weight: float = 1.0


DEFAULT_DIMENSIONS = [
    Dimension(
        id="financial",
        name="财务成长性",
        description="评估营收增长率、净利润增长率、ROE、毛利率、净利率等核心财务指标的增长趋势",
        weight=1.0,
    ),
    Dimension(
        id="industry",
        name="行业赛道",
        description="评估行业景气度、政策支持力度、市场空间、竞争格局等赛道因素",
        weight=1.0,
    ),
    Dimension(
        id="valuation",
        name="估值合理性",
        description="评估PE分位、PB分位、PEG等估值指标，判断当前价格是否合理",
        weight=1.0,
    ),
]


@dataclass(frozen=True)
class CustomDimension(Dimension):
    prompt_hint: str = ""
