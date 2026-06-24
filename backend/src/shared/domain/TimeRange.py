from datetime import date


class TimeRange:
    def __init__(self, start: date, end: date) -> None:
        if start > end:
            raise ValueError("Start date must be before or equal to end date")
        self._start = start
        self._end = end

    @property
    def start(self) -> date:
        return self._start

    @property
    def end(self) -> date:
        return self._end

    @staticmethod
    def years_back(n: int) -> "TimeRange":
        today = date.today()
        return TimeRange(start=today.replace(year=today.year - n), end=today)
