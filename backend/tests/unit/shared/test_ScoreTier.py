import pytest
from src.shared.domain.ScoreTier import ScoreTier, tier_from_score


class TestScoreTier:
    def test_tier_from_score_not_recommend_lower_bound(self):
        assert tier_from_score(0) == ScoreTier.NOT_RECOMMEND

    def test_tier_from_score_not_recommend_upper_bound(self):
        assert tier_from_score(59) == ScoreTier.NOT_RECOMMEND

    def test_tier_from_score_recommend_lower_bound(self):
        assert tier_from_score(60) == ScoreTier.RECOMMEND

    def test_tier_from_score_recommend_upper_bound(self):
        assert tier_from_score(79) == ScoreTier.RECOMMEND

    def test_tier_from_score_strongly_recommend_lower_bound(self):
        assert tier_from_score(80) == ScoreTier.STRONGLY_RECOMMEND

    def test_tier_from_score_strongly_recommend_upper_bound(self):
        assert tier_from_score(100) == ScoreTier.STRONGLY_RECOMMEND

    def test_tier_from_score_rejects_out_of_range(self):
        with pytest.raises(ValueError, match="Score must be between 0 and 100"):
            tier_from_score(-1)
        with pytest.raises(ValueError, match="Score must be between 0 and 100"):
            tier_from_score(101)

    def test_tier_label_chinese(self):
        assert ScoreTier.NOT_RECOMMEND.label == "不推荐"
        assert ScoreTier.RECOMMEND.label == "推荐"
        assert ScoreTier.STRONGLY_RECOMMEND.label == "力荐"
