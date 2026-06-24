from enum import Enum


class ScoreTier(Enum):
    NOT_RECOMMEND = "not_recommend"
    RECOMMEND = "recommend"
    STRONGLY_RECOMMEND = "strongly_recommend"

    @property
    def label(self) -> str:
        return _TIER_LABELS[self]

    @property
    def range(self) -> tuple[int, int]:
        return _TIER_RANGES[self]


_TIER_LABELS = {
    ScoreTier.NOT_RECOMMEND: "不推荐",
    ScoreTier.RECOMMEND: "推荐",
    ScoreTier.STRONGLY_RECOMMEND: "力荐",
}

_TIER_RANGES = {
    ScoreTier.NOT_RECOMMEND: (0, 59),
    ScoreTier.RECOMMEND: (60, 79),
    ScoreTier.STRONGLY_RECOMMEND: (80, 100),
}


def tier_from_score(score: float) -> ScoreTier:
    if not (0 <= score <= 100):
        raise ValueError(f"Score must be between 0 and 100, got {score}")
    if score >= 80:
        return ScoreTier.STRONGLY_RECOMMEND
    if score >= 60:
        return ScoreTier.RECOMMEND
    return ScoreTier.NOT_RECOMMEND
