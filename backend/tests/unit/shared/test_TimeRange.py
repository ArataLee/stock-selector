import pytest
from datetime import date
from src.shared.domain.TimeRange import TimeRange


class TestTimeRange:
    def test_valid_range(self):
        r = TimeRange(start=date(2024, 1, 1), end=date(2024, 12, 31))
        assert r.start == date(2024, 1, 1)
        assert r.end == date(2024, 12, 31)

    def test_start_after_end_raises(self):
        with pytest.raises(ValueError, match="Start date must be before or equal to end date"):
            TimeRange(start=date(2024, 12, 31), end=date(2024, 1, 1))

    def test_years_back(self):
        r = TimeRange.years_back(3)
        today = date.today()
        assert r.end == today
        assert r.start == today.replace(year=today.year - 3)

    def test_same_start_and_end_valid(self):
        d = date(2024, 6, 15)
        r = TimeRange(start=d, end=d)
        assert r.start == r.end == d
