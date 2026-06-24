# Phase 1: Foundation — Shared Kernel + Market + LLM + Screening + CLI

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Working CLI tool that queries A-share stock data via AKShare and scores stocks using LLM.

**Architecture:** DDD layered architecture — Shared Kernel value objects → Market Context (unified data API with multi-source degradation) → LLM Context (OpenAI-compatible multi-model) → Screening Context (orchestrates Market + LLM) → CLI presentation via Typer.

**Tech Stack:** Python 3.12+, Typer, httpx (async), pydantic v2, PyYAML, pytest

---

### Task 1: Project setup

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/config/default.yaml`
- Create: `backend/config/user.yaml.example`

- [ ] **Step 1: Write pyproject.toml**

```toml
[project]
name = "stock-selector"
version = "0.1.0"
description = "A股成长价值选股助手"
requires-python = ">=3.12"
dependencies = [
    "typer>=0.15",
    "httpx>=0.28",
    "pydantic>=2.10",
    "pyyaml>=6.0",
    "akshare>=1.17",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.25",
    "pytest-mock>=3.14",
    "pytest-httpx>=0.35",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

- [ ] **Step 2: Write default.yaml**

```yaml
market:
  data_sources:
    - id: akshare
      name: AKShare
      type: free
      priority: 2
      enabled: true
    - id: baostock
      name: Baostock
      type: free
      priority: 3
      enabled: true
    - id: tushare
      name: Tushare
      type: account
      priority: 1
      enabled: false

llm:
  providers: []
  scenario_routing:
    conversation: ${provider}
    scoring: ${provider}
    report: ${provider}

screening:
  default_dimensions: ["financial", "industry", "valuation"]
  composite_strategy: weighted
  universe_default: all
  batch_size: 20

notification:
  channels: []

scheduler:
  max_concurrent_monitors: 5
  default_cron: "0 18 * * 1-5"
```

- [ ] **Step 3: Write user.yaml.example**

```yaml
market:
  accounts:
    tushare:
      token: "your_tushare_token"

llm:
  providers:
    - id: deepseek
      api_base: https://api.deepseek.com/v1
      api_key: sk-your-key
      model: deepseek-chat
      default: true

notification:
  channels:
    - id: wecom_1
      type: wecom
      webhook_url: https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx
      enabled: true
```

- [ ] **Step 4: Install dependencies**

Run: `cd backend && pip install -e ".[dev]"`
Expected: packages installed successfully

- [ ] **Step 5: Commit**

```bash
git add backend/pyproject.toml backend/config/default.yaml backend/config/user.yaml.example
git commit -m "feat: project setup with dependencies and config"
```

---

### Task 2: Shared Kernel — ScoreTier enum

**Files:**
- Create: `backend/src/shared/__init__.py` (empty)
- Create: `backend/src/shared/domain/__init__.py` (empty)
- Create: `backend/src/shared/domain/ScoreTier.py`
- Create: `backend/tests/unit/shared/__init__.py` (empty)
- Create: `backend/tests/unit/shared/test_ScoreTier.py`

- [ ] **Step 1: Write failing test**

```python
# tests/unit/shared/test_ScoreTier.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/unit/shared/test_ScoreTier.py -v`
Expected: FAIL — ModuleNotFoundError

- [ ] **Step 3: Write implementation**

```python
# src/shared/domain/ScoreTier.py
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/unit/shared/test_ScoreTier.py -v`
Expected: 8 tests PASS

- [ ] **Step 5: Commit**

```bash
git add backend/src/shared/ backend/tests/unit/shared/
git commit -m "feat: add ScoreTier enum with Chinese labels and tier_from_score"
```

---

### Task 3: Shared Kernel — StockCode value object

**Files:**
- Create: `backend/src/shared/domain/StockCode.py`
- Create: `backend/tests/unit/shared/test_StockCode.py`

- [ ] **Step 1: Write failing test**

```python
# tests/unit/shared/test_StockCode.py
import pytest
from src.shared.domain.StockCode import StockCode
from src.shared.domain.Market import Market


class TestStockCode:
    def test_parse_shanghai_stock(self):
        code = StockCode("600001.SH")
        assert code.raw == "600001.SH"
        assert code.digits == "600001"
        assert code.market == Market.SH

    def test_parse_shenzhen_stock(self):
        code = StockCode("000001.SZ")
        assert code.digits == "000001"
        assert code.market == Market.SZ

    def test_parse_beijing_stock(self):
        code = StockCode("830001.BJ")
        assert code.digits == "830001"
        assert code.market == Market.BJ

    def test_from_digits_shanghai(self):
        code = StockCode.from_digits("600001")
        assert str(code) == "600001.SH"

    def test_from_digits_shenzhen(self):
        code = StockCode.from_digits("000001")
        assert str(code) == "000001.SZ"
        code2 = StockCode.from_digits("002001")
        assert str(code2) == "002001.SZ"

    def test_from_digits_beijing(self):
        code = StockCode.from_digits("830001")
        assert str(code) == "830001.BJ"

    def test_from_digits_kechuang(self):
        code = StockCode.from_digits("688001")
        assert str(code) == "688001.SH"

    def test_from_digits_chuangyeban(self):
        code = StockCode.from_digits("300001")
        assert str(code) == "300001.SZ"

    def test_equality(self):
        a = StockCode("600001.SH")
        b = StockCode.from_digits("600001")
        assert a == b
        assert hash(a) == hash(b)

    def test_invalid_format(self):
        with pytest.raises(ValueError, match="Invalid stock code format"):
            StockCode("abc")
        with pytest.raises(ValueError, match="Invalid stock code format"):
            StockCode("600001.XX")

    def test_invalid_digits_length(self):
        with pytest.raises(ValueError, match="Stock code digits must be 6 characters"):
            StockCode.from_digits("12345")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/unit/shared/test_StockCode.py -v`
Expected: FAIL — ModuleNotFoundError (Market not defined yet)

- [ ] **Step 3: Write Market enum first**

```python
# src/shared/domain/Market.py
from enum import Enum


class Market(Enum):
    SH = "SH"   # 上海
    SZ = "SZ"   # 深圳
    BJ = "BJ"   # 北京
```

- [ ] **Step 4: Write StockCode implementation**

```python
# src/shared/domain/StockCode.py
from __future__ import annotations
import re
from src.shared.domain.Market import Market

_SH_PREFIXES = {"6", "688"}
_SZ_PREFIXES = {"0", "2", "3"}  # 300开头创业板，002中小板，000主板
_BJ_PREFIXES = {"8", "4"}

_CODE_PATTERN = re.compile(r"^(\d{6})\.(SH|SZ|BJ)$")


class StockCode:
    def __init__(self, raw: str) -> None:
        m = _CODE_PATTERN.match(raw.upper())
        if not m:
            raise ValueError(f"Invalid stock code format: {raw}. Expected format: 600001.SH")
        self._digits = m.group(1)
        self._market = Market(m.group(2))
        self._raw = f"{self._digits}.{self._market.value}"

    @property
    def raw(self) -> str:
        return self._raw

    @property
    def digits(self) -> str:
        return self._digits

    @property
    def market(self) -> Market:
        return self._market

    @staticmethod
    def from_digits(digits: str) -> StockCode:
        if len(digits) != 6 or not digits.isdigit():
            raise ValueError("Stock code digits must be 6 characters")
        prefix = digits[:1]
        if digits.startswith("688") or prefix in _SH_PREFIXES:
            if prefix in _SH_PREFIXES:
                return StockCode(f"{digits}.SH")
        if digits.startswith("300") or prefix in _SZ_PREFIXES:
            if prefix in _SZ_PREFIXES:
                return StockCode(f"{digits}.SZ")
        if prefix in _BJ_PREFIXES:
            return StockCode(f"{digits}.BJ")
        return StockCode(f"{digits}.SH")  # fallback

    def __str__(self) -> str:
        return self._raw

    def __repr__(self) -> str:
        return f"StockCode({self._raw!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, StockCode):
            return NotImplemented
        return self._raw == other._raw

    def __hash__(self) -> int:
        return hash(self._raw)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/unit/shared/test_StockCode.py -v`
Expected: 11 tests PASS

- [ ] **Step 6: Commit**

```bash
git add backend/src/shared/domain/Market.py backend/src/shared/domain/StockCode.py backend/tests/unit/shared/test_StockCode.py
git commit -m "feat: add StockCode value object with market inference"
```

---

### Task 4: Shared Kernel — TimeRange and DomainError

**Files:**
- Create: `backend/src/shared/domain/TimeRange.py`
- Create: `backend/src/shared/exceptions/__init__.py` (empty)
- Create: `backend/src/shared/exceptions/DomainError.py`
- Create: `backend/tests/unit/shared/test_TimeRange.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/unit/shared/test_TimeRange.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/unit/shared/test_TimeRange.py -v`
Expected: FAIL — ModuleNotFoundError

- [ ] **Step 3: Write DomainError first**

```python
# src/shared/exceptions/DomainError.py
class DomainError(Exception):
    """Base class for all domain exceptions."""
    pass
```

- [ ] **Step 4: Write TimeRange**

```python
# src/shared/domain/TimeRange.py
from datetime import date, timedelta


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
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/unit/shared/test_TimeRange.py -v`
Expected: 4 tests PASS

- [ ] **Step 6: Commit**

```bash
git add backend/src/shared/domain/TimeRange.py backend/src/shared/exceptions/ backend/tests/unit/shared/test_TimeRange.py
git commit -m "feat: add TimeRange value object and DomainError base class"
```

---

### Task 5: Market Context — Domain entities and Repository interfaces

**Files:**
- Create: `backend/src/market/__init__.py` (empty)
- Create: `backend/src/market/domain/__init__.py` (empty)
- Create: `backend/src/market/domain/DataSource.py`
- Create: `backend/src/market/domain/Stock.py`
- Create: `backend/src/market/domain/MarketData.py`
- Create: `backend/src/market/domain/FinancialData.py`

- [ ] **Step 1: Write DataSource value objects**

```python
# src/market/domain/DataSource.py
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
        # DataSourceId is frozen, replace in list
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
```

- [ ] **Step 2: Write Stock aggregate and Repository interface**

```python
# src/market/domain/Stock.py
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from src.shared.domain.StockCode import StockCode
from src.shared.domain.Market import Market


@dataclass(frozen=True)
class Stock:
    code: StockCode
    name: str
    listing_date: date | None = None


class StockRepository(ABC):
    @abstractmethod
    async def find(self, code: StockCode) -> Stock | None:
        ...

    @abstractmethod
    async def search(self, keyword: str) -> list[Stock]:
        ...
```

- [ ] **Step 3: Write Quote and Repository**

```python
# src/market/domain/MarketData.py
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from src.shared.domain.StockCode import StockCode


@dataclass(frozen=True)
class Quote:
    code: StockCode
    name: str
    price: float
    pe_ttm: float | None = None
    pb: float | None = None
    market_cap: float | None = None  # 总市值（亿）
    volume: float | None = None
    trade_date: date | None = None


class QuoteRepository(ABC):
    @abstractmethod
    async def fetch_one(self, code: StockCode) -> Quote | None:
        ...

    @abstractmethod
    async def fetch_batch(self, codes: list[StockCode]) -> list[Quote]:
        ...
```

- [ ] **Step 4: Write FinancialReport and Repository**

```python
# src/market/domain/FinancialData.py
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from src.shared.domain.StockCode import StockCode


@dataclass(frozen=True)
class FinancialReport:
    code: StockCode
    period: str  # 报告期，如 "2024Q4"
    revenue_yoy: float | None = None  # 营收同比增长率（%）
    profit_yoy: float | None = None   # 归母净利润同比增长率（%）
    roe: float | None = None          # ROE（%）
    gross_margin: float | None = None # 毛利率（%）
    net_margin: float | None = None   # 净利率（%）


class FinancialRepository(ABC):
    @abstractmethod
    async def fetch(self, code: StockCode, periods: int = 4) -> list[FinancialReport]:
        ...

    @abstractmethod
    async def fetch_batch(self, codes: list[StockCode], periods: int = 4) -> dict[StockCode, list[FinancialReport]]:
        ...
```

- [ ] **Step 5: Commit**

```bash
git add backend/src/market/
git commit -m "feat: add Market Context domain entities and repository interfaces"
```

---

### Task 6: Market Context — AKShare Adapter

**Files:**
- Create: `backend/src/market/infrastructure/__init__.py` (empty)
- Create: `backend/src/market/infrastructure/adapters/__init__.py` (empty)
- Create: `backend/src/market/infrastructure/adapters/AKShareAdapter.py`

- [ ] **Step 1: Write AKShareAdapter**

```python
# src/market/infrastructure/adapters/AKShareAdapter.py
from datetime import date
from src.shared.domain.StockCode import StockCode
from src.market.domain.Stock import Stock, StockRepository
from src.market.domain.MarketData import Quote, QuoteRepository
from src.market.domain.FinancialData import FinancialReport, FinancialRepository


class AKShareAdapter(StockRepository, QuoteRepository, FinancialRepository):
    """AKShare数据源适配器。免费开源，开箱即用。"""

    async def find(self, code: StockCode) -> Stock | None:
        try:
            import akshare as ak
            info = ak.stock_individual_info_em(symbol=code.digits)
            if info is None or info.empty:
                return None
            name_row = info[info["item"] == "股票简称"]
            name = name_row["value"].iloc[0] if not name_row.empty else code.digits
            return Stock(code=code, name=str(name))
        except Exception:
            return None

    async def search(self, keyword: str) -> list[Stock]:
        # AKShare没有直接搜索接口，通过全量列表过滤
        return []

    async def fetch_one(self, code: StockCode) -> Quote | None:
        try:
            import akshare as ak
            df = ak.stock_zh_a_spot_em()
            row = df[df["代码"] == code.digits]
            if row.empty:
                return None
            r = row.iloc[0]
            return Quote(
                code=code,
                name=str(r.get("名称", code.digits)),
                price=float(r.get("最新价", 0)),
                pe_ttm=float(r["市盈率-动态"]) if r.get("市盈率-动态") else None,
                pb=float(r["市净率"]) if r.get("市净率") else None,
                market_cap=float(r["总市值"]) / 1e8 if r.get("总市值") else None,
                volume=float(r["成交量"]) if r.get("成交量") else None,
                trade_date=date.today(),
            )
        except Exception:
            return None

    async def fetch_batch(self, codes: list[StockCode]) -> list[Quote]:
        try:
            import akshare as ak
            df = ak.stock_zh_a_spot_em()
            code_set = {c.digits for c in codes}
            quotes: list[Quote] = []
            for _, r in df.iterrows():
                if r["代码"] in code_set:
                    qcode = next(c for c in codes if c.digits == r["代码"])
                    quotes.append(Quote(
                        code=qcode,
                        name=str(r.get("名称", qcode.digits)),
                        price=float(r.get("最新价", 0)),
                        pe_ttm=float(r["市盈率-动态"]) if r.get("市盈率-动态") else None,
                        pb=float(r["市净率"]) if r.get("市净率") else None,
                        market_cap=float(r["总市值"]) / 1e8 if r.get("总市值") else None,
                        trade_date=date.today(),
                    ))
            return quotes
        except Exception:
            return []

    async def fetch(self, code: StockCode, periods: int = 4) -> list[FinancialReport]:
        try:
            import akshare as ak
            df = ak.stock_financial_abstract_ths(symbol=code.digits, indicator="按报告期")
            if df is None or df.empty:
                return []
            reports: list[FinancialReport] = []
            for _, r in df.head(periods).iterrows():
                reports.append(FinancialReport(
                    code=code,
                    period=str(r.get("报告期", "")),
                    revenue_yoy=self._safe_float(r.get("营业总收入同比增长率")),
                    profit_yoy=self._safe_float(r.get("归母净利润同比增长率")),
                    roe=self._safe_float(r.get("净资产收益率")),
                    gross_margin=self._safe_float(r.get("销售毛利率")),
                    net_margin=self._safe_float(r.get("销售净利率")),
                ))
            return reports
        except Exception:
            return []

    async def fetch_batch(self, codes: list[StockCode], periods: int = 4) -> dict[StockCode, list[FinancialReport]]:
        result: dict[StockCode, list[FinancialReport]] = {}
        for code in codes:
            reports = await self.fetch(code, periods)
            if reports:
                result[code] = reports
        return result

    @staticmethod
    def _safe_float(value) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
```

- [ ] **Step 2: Commit**

```bash
git add backend/src/market/infrastructure/adapters/AKShareAdapter.py
git commit -m "feat: add AKShare adapter implementing all Market repositories"
```

---

### Task 7: Market Context — DataSourceRouter

**Files:**
- Create: `backend/src/market/infrastructure/DataSourceRouter.py`
- Create: `backend/tests/unit/market/__init__.py` (empty)
- Create: `backend/tests/unit/market/test_DataSourceRouter.py`

- [ ] **Step 1: Write failing test**

```python
# tests/unit/market/test_DataSourceRouter.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from src.shared.domain.StockCode import StockCode
from src.market.domain.DataSource import DataSourceId, DataSourceType
from src.market.domain.MarketData import Quote
from src.market.infrastructure.DataSourceRouter import QuoteRouter


class TestQuoteRouter:
    @pytest.fixture
    def adapter_a(self):
        adapter = MagicMock()
        adapter.fetch_one = AsyncMock()
        adapter.fetch_batch = AsyncMock()
        return adapter

    @pytest.fixture
    def adapter_b(self):
        adapter = MagicMock()
        adapter.fetch_one = AsyncMock()
        adapter.fetch_batch = AsyncMock()
        return adapter

    @pytest.mark.asyncio
    async def test_first_adapter_succeeds(self, adapter_a, adapter_b):
        code = StockCode("600001.SH")
        quote = Quote(code=code, name="测试", price=10.0)
        adapter_a.fetch_batch.return_value = [quote]

        router = QuoteRouter(adapters=[adapter_a, adapter_b])
        results = await router.fetch_batch([code])

        assert results == [quote]
        adapter_a.fetch_batch.assert_called_once()
        adapter_b.fetch_batch.assert_not_called()

    @pytest.mark.asyncio
    async def test_fallback_when_first_fails(self, adapter_a, adapter_b):
        code = StockCode("600001.SH")
        quote = Quote(code=code, name="测试", price=10.0)
        adapter_a.fetch_batch.return_value = []  # fails
        adapter_b.fetch_batch.return_value = [quote]

        router = QuoteRouter(adapters=[adapter_a, adapter_b])
        results = await router.fetch_batch([code])

        assert results == [quote]
        adapter_a.fetch_batch.assert_called_once()
        adapter_b.fetch_batch.assert_called_once()

    @pytest.mark.asyncio
    async def test_all_adapters_fail(self, adapter_a, adapter_b):
        code = StockCode("600001.SH")
        adapter_a.fetch_batch.return_value = []
        adapter_b.fetch_batch.return_value = []

        router = QuoteRouter(adapters=[adapter_a, adapter_b])
        results = await router.fetch_batch([code])

        assert results == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/unit/market/test_DataSourceRouter.py -v`
Expected: FAIL — ModuleNotFoundError

- [ ] **Step 3: Write DataSourceRouter**

```python
# src/market/infrastructure/DataSourceRouter.py
from src.shared.domain.StockCode import StockCode
from src.market.domain.Stock import Stock, StockRepository
from src.market.domain.MarketData import Quote, QuoteRepository
from src.market.domain.FinancialData import FinancialReport, FinancialRepository


class StockRouter(StockRepository):
    def __init__(self, adapters: list[StockRepository]) -> None:
        self._adapters = adapters

    async def find(self, code: StockCode) -> Stock | None:
        for adapter in self._adapters:
            result = await adapter.find(code)
            if result is not None:
                return result
        return None

    async def search(self, keyword: str) -> list[Stock]:
        for adapter in self._adapters:
            result = await adapter.search(keyword)
            if result:
                return result
        return []


class QuoteRouter(QuoteRepository):
    def __init__(self, adapters: list[QuoteRepository]) -> None:
        self._adapters = adapters

    async def fetch_one(self, code: StockCode) -> Quote | None:
        for adapter in self._adapters:
            result = await adapter.fetch_one(code)
            if result is not None:
                return result
        return None

    async def fetch_batch(self, codes: list[StockCode]) -> list[Quote]:
        for adapter in self._adapters:
            result = await adapter.fetch_batch(codes)
            if result:
                return result
        return []


class FinancialRouter(FinancialRepository):
    def __init__(self, adapters: list[FinancialRepository]) -> None:
        self._adapters = adapters

    async def fetch(self, code: StockCode, periods: int = 4) -> list[FinancialReport]:
        for adapter in self._adapters:
            result = await adapter.fetch(code, periods)
            if result:
                return result
        return []

    async def fetch_batch(self, codes: list[StockCode], periods: int = 4) -> dict[StockCode, list[FinancialReport]]:
        for adapter in self._adapters:
            result = await adapter.fetch_batch(codes, periods)
            if result:
                return result
        return {}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/unit/market/test_DataSourceRouter.py -v`
Expected: 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add backend/src/market/infrastructure/DataSourceRouter.py backend/tests/unit/market/
git commit -m "feat: add DataSourceRouter with fallback degradation"
```

---

### Task 8: Market Context — Application services

**Files:**
- Create: `backend/src/market/application/__init__.py` (empty)
- Create: `backend/src/market/application/QuoteQueryService.py`

- [ ] **Step 1: Write QuoteQueryService**

```python
# src/market/application/QuoteQueryService.py
from src.shared.domain.StockCode import StockCode
from src.market.domain.MarketData import Quote, QuoteRepository


class QuoteQueryService:
    def __init__(self, quote_repo: QuoteRepository) -> None:
        self._repo = quote_repo

    async def get_quote(self, code_str: str) -> Quote | None:
        code = StockCode(code_str)
        return await self._repo.fetch_one(code)

    async def get_quotes(self, code_strs: list[str]) -> list[Quote]:
        codes = [StockCode(s) for s in code_strs]
        return await self._repo.fetch_batch(codes)
```

- [ ] **Step 2: Commit**

```bash
git add backend/src/market/application/
git commit -m "feat: add QuoteQueryService application layer"
```

---

### Task 9: LLM Context — Domain

**Files:**
- Create: `backend/src/llm/__init__.py` (empty)
- Create: `backend/src/llm/domain/__init__.py` (empty)
- Create: `backend/src/llm/domain/ModelProvider.py`
- Create: `backend/src/llm/domain/Scenario.py`
- Create: `backend/src/llm/domain/Analysis.py`
- Create: `backend/src/llm/domain/Prompt.py`

- [ ] **Step 1: Write ModelProvider**

```python
# src/llm/domain/ModelProvider.py
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum


class ProviderId(str, Enum):
    DEEPSEEK = "deepseek"
    QWEN = "qwen"
    OPENAI = "openai"
    OLLAMA = "ollama"
    CUSTOM = "custom"


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
```

- [ ] **Step 2: Write Scenario**

```python
# src/llm/domain/Scenario.py
from dataclasses import dataclass
from enum import Enum


class ScenarioType(Enum):
    CONVERSATION = "conversation"
    SCORING = "scoring"
    REPORT = "report"


@dataclass(frozen=True)
class ScenarioConfig:
    scenario: ScenarioType
    provider_id: str  # 绑定到哪个provider
    provider_override: str | None = None  # 允许用户为特定场景指定不同provider
```

- [ ] **Step 3: Write Analysis (ScoreCard + StockAnalysis)**

```python
# src/llm/domain/Analysis.py
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from src.shared.domain.StockCode import StockCode
from src.shared.domain.ScoreTier import ScoreTier, tier_from_score


@dataclass
class ScoreCard:
    dimension_scores: dict[str, float]  # {"财务": 75, "行业": 82, "估值": 60}
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
```

- [ ] **Step 4: Write Prompt template**

```python
# src/llm/domain/Prompt.py
from dataclasses import dataclass, field


@dataclass
class PromptTemplate:
    template_id: str
    scenario: str
    content: str
    description: str = ""
    variables: list[str] = field(default_factory=list)


# 内置默认Prompt
DEFAULT_SCORING_PROMPT = PromptTemplate(
    template_id="default_scoring",
    scenario="scoring",
    description="默认多维度综合评分模板",
    content="""你是一位专业的A股成长股投资分析师。请对以下股票进行多维度成长价值评估。

## 股票信息
- 代码: {stock_code}
- 名称: {stock_name}
- 最新价: {price}元
- PE(TTM): {pe_ttm}
- PB: {pb}
- 总市值: {market_cap}亿

## 近几期财务数据
{financial_data}

## 评估维度
{dimensions}

## 评分规则
请对每个维度打分（0-100分），然后给出综合评分（0-100分），并提供推荐理由。
评分标准：
- 0-60分：成长性不足，不推荐
- 60-80分：有一定成长价值，推荐
- 80-100分：成长价值突出，力荐

## 输出格式（严格JSON）
```json
{
  "dimension_scores": {"维度名": 分数, ...},
  "composite_score": 综合分数,
  "reasoning": "推荐理由，200字以内"
}
```

请直接输出JSON，不要包含其他内容。""",
    variables=["stock_code", "stock_name", "price", "pe_ttm", "pb", "market_cap", "financial_data", "dimensions"],
)


DEFAULT_CHAT_PROMPT = PromptTemplate(
    template_id="default_chat",
    scenario="conversation",
    description="默认对话模板",
    content="""你是一位专业的A股投资顾问，擅长帮助投资新手分析股票的成长价值。
你可以：分析股票基本面、解读财务数据、评估成长潜力、回答选股相关问题。
请用通俗易懂的语言回答，避免过多专业术语。

当前上下文：
{context}

用户问题：{question}""",
    variables=["context", "question"],
)


BUILTIN_PROMPTS: dict[str, PromptTemplate] = {
    "default_scoring": DEFAULT_SCORING_PROMPT,
    "default_chat": DEFAULT_CHAT_PROMPT,
}
```

- [ ] **Step 5: Commit**

```bash
git add backend/src/llm/domain/
git commit -m "feat: add LLM Context domain — providers, scenarios, prompts, analysis"
```

---

### Task 10: LLM Context — OpenAI Compatible Adapter

**Files:**
- Create: `backend/src/llm/infrastructure/__init__.py` (empty)
- Create: `backend/src/llm/infrastructure/clients/__init__.py` (empty)
- Create: `backend/src/llm/infrastructure/clients/LLMClient.py`
- Create: `backend/src/llm/infrastructure/adapters/__init__.py` (empty)
- Create: `backend/src/llm/infrastructure/adapters/OpenAICompatAdapter.py`

- [ ] **Step 1: Write LLMClient (httpx wrapper)**

```python
# src/llm/infrastructure/clients/LLMClient.py
import json
import httpx
from src.llm.domain.ModelProvider import ProviderConfig


class LLMClient:
    def __init__(self, provider: ProviderConfig, timeout: float = 60.0) -> None:
        self._provider = provider
        self._client = httpx.AsyncClient(
            base_url=provider.api_base.rstrip("/"),
            headers={
                "Authorization": f"Bearer {provider.api_key}",
                "Content-Type": "application/json",
            },
            timeout=timeout,
        )

    async def chat(
        self,
        messages: list[dict],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        temp = temperature if temperature is not None else self._provider.temperature
        max_tok = max_tokens if max_tokens is not None else self._provider.max_tokens

        response = await self._client.post(
            "/chat/completions",
            json={
                "model": self._provider.model,
                "messages": messages,
                "temperature": temp,
                "max_tokens": max_tok,
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

    async def chat_stream(
        self,
        messages: list[dict],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ):
        temp = temperature if temperature is not None else self._provider.temperature
        max_tok = max_tokens if max_tokens is not None else self._provider.max_tokens

        async with self._client.stream(
            "POST",
            "/chat/completions",
            json={
                "model": self._provider.model,
                "messages": messages,
                "temperature": temp,
                "max_tokens": max_tok,
                "stream": True,
            },
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break
                    chunk = json.loads(data_str)
                    delta = chunk["choices"][0].get("delta", {})
                    if "content" in delta:
                        yield delta["content"]

    async def close(self) -> None:
        await self._client.aclose()
```

- [ ] **Step 2: Write OpenAICompatAdapter**

```python
# src/llm/infrastructure/adapters/OpenAICompatAdapter.py
import json
import re
from src.llm.domain.ModelProvider import ProviderConfig, ProviderRegistry
from src.llm.domain.Scenario import ScenarioType
from src.llm.domain.Prompt import PromptTemplate, BUILTIN_PROMPTS
from src.llm.domain.Analysis import ScoreCard
from src.llm.infrastructure.clients.LLMClient import LLMClient


class OpenAICompatAdapter:
    def __init__(self, registry: ProviderRegistry) -> None:
        self._registry = registry
        self._clients: dict[str, LLMClient] = {}

    def _get_client(self, provider_id: str | None = None) -> LLMClient:
        if provider_id:
            cfg = self._registry.find(provider_id)
        else:
            cfg = self._registry.default()
        if cfg is None:
            raise RuntimeError("No LLM provider configured. Please configure one in settings.")
        if cfg.id not in self._clients:
            self._clients[cfg.id] = LLMClient(cfg)
        return self._clients[cfg.id]

    async def score_stock(self, prompt_template: PromptTemplate, variables: dict, provider_id: str | None = None) -> ScoreCard:
        client = self._get_client(provider_id)
        content = prompt_template.content.format(**variables)
        messages = [{"role": "user", "content": content}]

        raw_response = await client.chat(messages, temperature=0.3, max_tokens=1024)
        return self._extract_score_card(raw_response)

    async def score_stocks_batch(
        self,
        prompt_template: PromptTemplate,
        variables_list: list[dict],
        provider_id: str | None = None,
    ) -> list[ScoreCard | None]:
        results: list[ScoreCard | None] = []
        for variables in variables_list:
            try:
                card = await self.score_stock(prompt_template, variables, provider_id)
                results.append(card)
            except Exception:
                results.append(None)
        return results

    async def chat(self, messages: list[dict], provider_id: str | None = None):
        client = self._get_client(provider_id)
        async for token in client.chat_stream(messages):
            yield token

    async def generate_report(self, stocks_data: list[dict], provider_id: str | None = None) -> str:
        client = self._get_client(provider_id)
        stock_summaries = "\n".join(
            f"- {s['name']}({s['code']}): 综合评分{s['score']}, {s['tier']}, {s['reasoning'][:100]}"
            for s in stocks_data
        )
        prompt = f"""请根据以下A股成长股筛选结果，生成一份简洁的投资分析报告。

## 筛选结果
{stock_summaries}

## 要求
1. 先总体概述筛选结果
2. 分析评分最高的3-5只股票
3. 给出风险提示（面向投资新手）
4. 使用Markdown格式，500字以内"""

        messages = [{"role": "user", "content": prompt}]
        return await client.chat(messages, temperature=0.5, max_tokens=2000)

    def _extract_score_card(self, raw: str) -> ScoreCard:
        # Try to extract JSON from response
        json_match = re.search(r'\{[\s\S]*\}', raw)
        if json_match:
            data = json.loads(json_match.group())
            return ScoreCard.from_llm_output(data)

        # Retry: if no JSON found, try a stricter approach
        raise ValueError(f"Failed to extract ScoreCard from LLM response: {raw[:200]}...")

    async def close(self) -> None:
        for client in self._clients.values():
            await client.close()
```

- [ ] **Step 3: Commit**

```bash
git add backend/src/llm/infrastructure/
git commit -m "feat: add LLMClient and OpenAICompatAdapter with scoring and chat"
```

---

### Task 11: Screening Context — Domain

**Files:**
- Create: `backend/src/screening/__init__.py` (empty)
- Create: `backend/src/screening/domain/__init__.py` (empty)
- Create: `backend/src/screening/domain/Dimension.py`
- Create: `backend/src/screening/domain/ScreenResult.py`

- [ ] **Step 1: Write Dimension and ScreenResult**

```python
# src/screening/domain/Dimension.py
from __future__ import annotations
from dataclasses import dataclass, field
from src.llm.domain.Prompt import PromptTemplate


@dataclass(frozen=True)
class Dimension:
    id: str
    name: str
    description: str
    weight: float = 1.0  # 在综合评分中的权重


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
    prompt_hint: str = ""  # 用户自定义的评估提示
```

```python
# src/screening/domain/ScreenResult.py
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
```

- [ ] **Step 2: Commit**

```bash
git add backend/src/screening/domain/
git commit -m "feat: add Screening domain — dimensions and ScreenResult"
```

---

### Task 12: Screening Context — ScreenStockUseCase (core orchestration)

**Files:**
- Create: `backend/src/screening/application/__init__.py` (empty)
- Create: `backend/src/screening/application/ScreenStockUseCase.py`

- [ ] **Step 1: Write ScreenStockUseCase**

```python
# src/screening/application/ScreenStockUseCase.py
from src.shared.domain.StockCode import StockCode
from src.market.domain.MarketData import QuoteRepository
from src.market.domain.FinancialData import FinancialRepository
from src.llm.domain.Prompt import BUILTIN_PROMPTS
from src.llm.domain.Analysis import ScoreCard
from src.llm.infrastructure.adapters.OpenAICompatAdapter import OpenAICompatAdapter
from src.screening.domain.Dimension import Dimension, DEFAULT_DIMENSIONS
from src.screening.domain.ScreenResult import ScreenResult


class ScreenStockUseCase:
    def __init__(
        self,
        quote_repo: QuoteRepository,
        financial_repo: FinancialRepository,
        llm_adapter: OpenAICompatAdapter,
    ) -> None:
        self._quote_repo = quote_repo
        self._financial_repo = financial_repo
        self._llm = llm_adapter

    async def screen_single(self, code_str: str, dimensions: list[Dimension] | None = None) -> ScreenResult | None:
        code = StockCode(code_str)
        dims = dimensions or DEFAULT_DIMENSIONS

        # 1. 获取行情
        quote = await self._quote_repo.fetch_one(code)
        if quote is None:
            return None

        # 2. 获取财务数据
        reports = await self._financial_repo.fetch(code, periods=4)

        # 3. 构建Prompt变量
        fin_text = self._format_financials(reports)
        dims_text = "\n".join(f"- {d.name}: {d.description}" for d in dims)

        variables = {
            "stock_code": str(code),
            "stock_name": quote.name,
            "price": f"{quote.price:.2f}",
            "pe_ttm": f"{quote.pe_ttm:.1f}" if quote.pe_ttm else "N/A",
            "pb": f"{quote.pb:.2f}" if quote.pb else "N/A",
            "market_cap": f"{quote.market_cap:.0f}" if quote.market_cap else "N/A",
            "financial_data": fin_text or "暂无财务数据",
            "dimensions": dims_text,
        }

        # 4. LLM打分
        template = BUILTIN_PROMPTS["default_scoring"]
        score_card = await self._llm.score_stock(template, variables)

        return ScreenResult(
            stock_code=code,
            stock_name=quote.name,
            score_card=score_card,
        )

    async def screen_batch(self, code_strs: list[str], dimensions: list[Dimension] | None = None) -> list[ScreenResult]:
        codes = [StockCode(s) for s in code_strs]
        dims = dimensions or DEFAULT_DIMENSIONS

        # 1. 批量获取行情
        quotes = await self._quote_repo.fetch_batch(codes)
        quote_map = {q.code: q for q in quotes}

        # 2. 批量获取财务数据
        fin_map = await self._financial_repo.fetch_batch(codes, periods=4)

        # 3. 逐个LLM打分
        template = BUILTIN_PROMPTS["default_scoring"]
        dims_text = "\n".join(f"- {d.name}: {d.description}" for d in dims)

        results: list[ScreenResult] = []
        for code in codes:
            quote = quote_map.get(code)
            if quote is None:
                continue

            reports = fin_map.get(code, [])
            fin_text = self._format_financials(reports)

            variables = {
                "stock_code": str(code),
                "stock_name": quote.name,
                "price": f"{quote.price:.2f}",
                "pe_ttm": f"{quote.pe_ttm:.1f}" if quote.pe_ttm else "N/A",
                "pb": f"{quote.pb:.2f}" if quote.pb else "N/A",
                "market_cap": f"{quote.market_cap:.0f}" if quote.market_cap else "N/A",
                "financial_data": fin_text or "暂无财务数据",
                "dimensions": dims_text,
            }

            try:
                score_card = await self._llm.score_stock(template, variables)
                results.append(ScreenResult(
                    stock_code=code,
                    stock_name=quote.name,
                    score_card=score_card,
                ))
            except Exception:
                continue

        # 4. 按综合评分降序
        results.sort(key=lambda r: r.composite_score, reverse=True)
        return results

    @staticmethod
    def _format_financials(reports) -> str:
        if not reports:
            return "暂无财务数据"
        lines = []
        for r in reports:
            lines.append(
                f"  {r.period}: "
                f"营收同比{r.revenue_yoy:.1f}% " if r.revenue_yoy else f"  {r.period}: 营收同比N/A "
                f"净利同比{r.profit_yoy:.1f}% " if r.profit_yoy else "净利同比N/A "
                f"ROE={r.roe:.1f}% " if r.roe else "ROE=N/A "
                f"毛利率={r.gross_margin:.1f}%" if r.gross_margin else "毛利率=N/A"
            )
        return "\n".join(lines)
```

- [ ] **Step 2: Commit**

```bash
git add backend/src/screening/application/
git commit -m "feat: add ScreenStockUseCase orchestrating Market + LLM"
```

---

### Task 13: Bootstrap — DI wiring and config loading

**Files:**
- Create: `backend/src/bootstrap.py`

- [ ] **Step 1: Write bootstrap**

```python
# src/bootstrap.py
from __future__ import annotations
import os
import yaml
from pathlib import Path
from src.market.domain.DataSource import DataSourceRegistry
from src.market.infrastructure.adapters.AKShareAdapter import AKShareAdapter
from src.market.infrastructure.DataSourceRouter import QuoteRouter, FinancialRouter
from src.llm.domain.ModelProvider import ProviderRegistry, ProviderConfig
from src.llm.infrastructure.adapters.OpenAICompatAdapter import OpenAICompatAdapter
from src.market.application.QuoteQueryService import QuoteQueryService
from src.screening.application.ScreenStockUseCase import ScreenStockUseCase


class AppContext:
    def __init__(self) -> None:
        self.config: dict = {}
        self.data_source_registry: DataSourceRegistry | None = None
        self.provider_registry: ProviderRegistry | None = None
        self.quote_router: QuoteRouter | None = None
        self.financial_router: FinancialRouter | None = None
        self.llm_adapter: OpenAICompatAdapter | None = None
        self.quote_service: QuoteQueryService | None = None
        self.screen_usecase: ScreenStockUseCase | None = None


def load_config(config_dir: str) -> dict:
    """加载配置：user.yaml > default.yaml"""
    base = Path(config_dir)

    # 加载默认配置
    default_path = base / "default.yaml"
    if not default_path.exists():
        raise FileNotFoundError(f"Default config not found: {default_path}")
    with open(default_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # 合并用户配置
    user_path = base / "user.yaml"
    if user_path.exists():
        with open(user_path, encoding="utf-8") as f:
            user_cfg = yaml.safe_load(f)
        _deep_merge(config, user_cfg)

    return config


def _deep_merge(base: dict, override: dict) -> None:
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        elif key in base and isinstance(base[key], list) and isinstance(value, list):
            base[key].extend(value)
        else:
            base[key] = value


def bootstrap(config_dir: str | None = None) -> AppContext:
    if config_dir is None:
        config_dir = os.environ.get(
            "STOCK_SELECTOR_CONFIG",
            str(Path(__file__).parent.parent / "config"),
        )

    ctx = AppContext()
    ctx.config = load_config(config_dir)

    # Market: DataSource Registry + Routers
    market_cfg = ctx.config.get("market", {})
    ds_cfgs = market_cfg.get("data_sources", [])
    ctx.data_source_registry = DataSourceRegistry.from_config_list(ds_cfgs)

    # 检查用户账号配置，自动启用account类型数据源
    accounts = market_cfg.get("accounts", {})
    akshare = AKShareAdapter()
    adapters = [akshare]

    if "tushare" in accounts:
        try:
            import tushare as ts  # noqa: F401
            from src.market.infrastructure.adapters.TushareAdapter import TushareAdapter
            token = accounts["tushare"]["token"]
            adapters.insert(0, TushareAdapter(token))
            ctx.data_source_registry.enable("tushare")
        except ImportError:
            pass

    ctx.quote_router = QuoteRouter(adapters)
    ctx.financial_router = FinancialRouter(adapters)

    # Market Application
    ctx.quote_service = QuoteQueryService(ctx.quote_router)

    # LLM: Provider Registry + Adapter
    llm_cfg = ctx.config.get("llm", {})
    ctx.provider_registry = ProviderRegistry()
    for p_cfg in llm_cfg.get("providers", []):
        ctx.provider_registry.add(ProviderConfig(**p_cfg))

    ctx.llm_adapter = OpenAICompatAdapter(ctx.provider_registry)

    # Screening Application
    ctx.screen_usecase = ScreenStockUseCase(
        quote_repo=ctx.quote_router,
        financial_repo=ctx.financial_router,
        llm_adapter=ctx.llm_adapter,
    )

    return ctx
```

- [ ] **Step 2: Commit**

```bash
git add backend/src/bootstrap.py
git commit -m "feat: add bootstrap DI wiring and config loading"
```

---

### Task 14: CLI — Market commands

**Files:**
- Create: `backend/src/cli/__init__.py` (empty)
- Create: `backend/src/cli/main.py`
- Create: `backend/src/cli/commands/__init__.py` (empty)
- Create: `backend/src/cli/commands/market.py`

- [ ] **Step 1: Write market CLI commands**

```python
# src/cli/commands/market.py
import typer
from src.cli.main import get_app_context
from src.shared.domain.StockCode import StockCode

market_app = typer.Typer(help="市场数据查询")


@market_app.command("quote")
def quote(
    code: str = typer.Argument(..., help="股票代码，如 600001.SH"),
):
    """查询实时行情"""
    ctx = get_app_context()
    import asyncio

    async def _run():
        svc = ctx.quote_service
        q = await svc.get_quote(code)
        if q is None:
            typer.echo(f"未找到股票行情: {code}")
            return
        typer.echo(f"股票: {q.name} ({q.code})")
        typer.echo(f"最新价: {q.price:.2f}元")
        if q.pe_ttm:
            typer.echo(f"PE(TTM): {q.pe_ttm:.1f}")
        if q.pb:
            typer.echo(f"PB: {q.pb:.2f}")
        if q.market_cap:
            typer.echo(f"总市值: {q.market_cap:.0f}亿")

    asyncio.run(_run())
```

- [ ] **Step 2: Write CLI main.py**

```python
# src/cli/main.py
import typer
from src.bootstrap import AppContext

_app_ctx: AppContext | None = None


def get_app_context() -> AppContext:
    global _app_ctx
    if _app_ctx is None:
        _app_ctx = AppContext()
        # For CLI, defer full bootstrap to when config dir is known
    return _app_ctx


app = typer.Typer(
    name="stock-selector",
    help="A股成长价值选股助手",
)


@app.callback()
def main(
    config_dir: str = typer.Option(
        None, "--config-dir", "-c",
        help="配置文件目录",
    ),
):
    global _app_ctx
    from src.bootstrap import bootstrap
    _app_ctx = bootstrap(config_dir)


from src.cli.commands.market import market_app  # noqa: E402

app.add_typer(market_app, name="market")


def run():
    app()


if __name__ == "__main__":
    run()
```

- [ ] **Step 3: Add CLI entry point to pyproject.toml**

Edit `backend/pyproject.toml`, add after `[project]`:

```toml
[project.scripts]
stock-selector = "src.cli.main:run"
```

- [ ] **Step 4: Commit**

```bash
git add backend/src/cli/
git commit -m "feat: add CLI main entry and market quote command"
```

---

### Task 15: CLI — Screening command

**Files:**
- Create: `backend/src/cli/commands/screening.py`

- [ ] **Step 1: Write screening CLI commands**

```python
# src/cli/commands/screening.py
import asyncio
import typer
from src.cli.main import get_app_context
from src.screening.domain.Dimension import DEFAULT_DIMENSIONS

screening_app = typer.Typer(help="选股筛选")


@screening_app.command("screen")
def screen(
    codes: list[str] = typer.Argument(..., help="股票代码列表，如 600001.SH 000001.SZ"),
    dimensions: str = typer.Option(
        "default", "--dimensions", "-d",
        help="评估维度: default(综合), financial(财务), industry(行业), valuation(估值)",
    ),
):
    """对指定股票进行成长价值评分"""
    ctx = get_app_context()

    if ctx.provider_registry.default() is None:
        typer.echo("错误：未配置LLM。请先配置LLM provider。", err=True)
        raise typer.Exit(1)

    # 选择维度
    if dimensions == "default":
        dims = DEFAULT_DIMENSIONS
    else:
        dim_keys = dimensions.split(",")
        dims = [d for d in DEFAULT_DIMENSIONS if d.id in dim_keys]
        if not dims:
            typer.echo(f"未知维度: {dimensions}", err=True)
            raise typer.Exit(1)

    async def _run():
        results = await ctx.screen_usecase.screen_batch(codes, dims)

        if not results:
            typer.echo("未能获取任何评分结果。")
            return

        typer.echo(f"\n{'='*60}")
        typer.echo(f"  成长价值评估结果（共{len(results)}只）")
        typer.echo(f"{'='*60}\n")

        for i, r in enumerate(results, 1):
            tier_icon = {"不推荐": "🔴", "推荐": "🟡", "力荐": "🟢"}.get(r.tier.label, "")
            typer.echo(f"{i}. {tier_icon} {r.stock_name} ({r.stock_code})")
            typer.echo(f"   综合评分: {r.composite_score:.0f}  [{r.tier.label}]")

            if r.score_card.dimension_scores:
                dim_str = " | ".join(
                    f"{k}: {v:.0f}" for k, v in r.score_card.dimension_scores.items()
                )
                typer.echo(f"   各维度: {dim_str}")

            typer.echo(f"   理由: {r.reasoning[:200]}")
            typer.echo("")

    asyncio.run(_run())


@screening_app.command("analyze")
def analyze(
    code: str = typer.Argument(..., help="股票代码，如 600001.SH"),
):
    """深度分析单只股票"""
    ctx = get_app_context()

    if ctx.provider_registry.default() is None:
        typer.echo("错误：未配置LLM。请先配置LLM provider。", err=True)
        raise typer.Exit(1)

    async def _run():
        result = await ctx.screen_usecase.screen_single(code)
        if result is None:
            typer.echo(f"无法获取 {code} 的数据。", err=True)
            return

        typer.echo(f"\n{'='*60}")
        typer.echo(f"  {result.stock_name} ({result.stock_code}) 深度分析")
        typer.echo(f"{'='*60}\n")
        typer.echo(f"综合评分: {result.composite_score:.0f}  [{result.tier.label}]\n")

        if result.score_card.dimension_scores:
            typer.echo("各维度评分:")
            for k, v in result.score_card.dimension_scores.items():
                bar = "█" * int(v / 5) + "░" * (20 - int(v / 5))
                typer.echo(f"  {k:12s} [{bar}] {v:.0f}")
            typer.echo("")

        typer.echo(f"推荐理由:\n{result.reasoning}\n")

    asyncio.run(_run())
```

- [ ] **Step 2: Register screening app in main.py**

Edit `backend/src/cli/main.py`, add after the market import lines:

```python
from src.cli.commands.screening import screening_app

app.add_typer(screening_app, name="screening")
```

- [ ] **Step 3: Commit**

```bash
git add backend/src/cli/commands/screening.py
git commit -m "feat: add CLI screening commands — screen and analyze"
```

---

### Task 16: Integration smoke test

**Files:**
- Create: `backend/tests/integration/__init__.py` (empty)
- Create: `backend/tests/integration/test_cli_smoke.py`

- [ ] **Step 1: Write smoke test**

```python
# tests/integration/test_cli_smoke.py
import sys
import pytest
from pathlib import Path

# Ensure backend src is on path
SRC = str(Path(__file__).parent.parent.parent / "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)


class TestCLIImports:
    def test_shared_kernel_imports(self):
        from src.shared.domain.StockCode import StockCode
        from src.shared.domain.Market import Market
        from src.shared.domain.ScoreTier import ScoreTier, tier_from_score
        from src.shared.domain.TimeRange import TimeRange

        code = StockCode.from_digits("600001")
        assert code.market == Market.SH
        assert tier_from_score(85) == ScoreTier.STRONGLY_RECOMMEND

    def test_market_domain_imports(self):
        from src.market.domain.Stock import Stock, StockRepository
        from src.market.domain.MarketData import Quote, QuoteRepository
        from src.market.domain.FinancialData import FinancialReport, FinancialRepository
        from src.market.domain.DataSource import DataSourceId, DataSourceType, DataSourceRegistry

        cfg = {"id": "test", "name": "Test", "type": "free", "priority": 1, "enabled": True}
        ds_id = DataSourceId.from_config(cfg)
        assert ds_id.type == DataSourceType.FREE

    def test_llm_domain_imports(self):
        from src.llm.domain.ModelProvider import ProviderRegistry, ProviderConfig
        from src.llm.domain.Scenario import ScenarioType
        from src.llm.domain.Analysis import ScoreCard
        from src.llm.domain.Prompt import BUILTIN_PROMPTS

        assert "default_scoring" in BUILTIN_PROMPTS
        assert "default_chat" in BUILTIN_PROMPTS

    def test_screening_imports(self):
        from src.screening.domain.Dimension import DEFAULT_DIMENSIONS
        from src.screening.domain.ScreenResult import ScreenResult

        assert len(DEFAULT_DIMENSIONS) == 3

    def test_bootstrap_imports(self):
        from src.bootstrap import load_config, AppContext

        config_dir = str(Path(__file__).parent.parent.parent / "config")
        config = load_config(config_dir)
        assert "market" in config
        assert "llm" in config
        assert "screening" in config

    def test_typer_app(self):
        from src.cli.main import app
        assert app is not None
```

- [ ] **Step 2: Run smoke test**

Run: `cd backend && python -m pytest tests/integration/test_cli_smoke.py -v`
Expected: 6 tests PASS

- [ ] **Step 3: Commit**

```bash
git add backend/tests/integration/
git commit -m "test: add integration smoke tests for all imports"
```

---

### Task 17: Tushare adapter (stub, activated by config)

**Files:**
- Create: `backend/src/market/infrastructure/adapters/TushareAdapter.py`

- [ ] **Step 1: Write TushareAdapter**

```python
# src/market/infrastructure/adapters/TushareAdapter.py
from datetime import date
from src.shared.domain.StockCode import StockCode
from src.market.domain.Stock import Stock, StockRepository
from src.market.domain.MarketData import Quote, QuoteRepository
from src.market.domain.FinancialData import FinancialReport, FinancialRepository


class TushareAdapter(StockRepository, QuoteRepository, FinancialRepository):
    """Tushare数据源适配器。需要token配置。"""

    def __init__(self, token: str) -> None:
        self._token = token
        self._pro = None

    def _get_pro(self):
        if self._pro is None:
            import tushare as ts
            ts.set_token(self._token)
            self._pro = ts.pro_api()
        return self._pro

    async def find(self, code: StockCode) -> Stock | None:
        try:
            pro = self._get_pro()
            df = pro.stock_basic(ts_code=str(code), fields="ts_code,name,list_date")
            if df.empty:
                return None
            row = df.iloc[0]
            listing = date.fromisoformat(str(row["list_date"])) if row["list_date"] else None
            return Stock(code=code, name=str(row["name"]), listing_date=listing)
        except Exception:
            return None

    async def search(self, keyword: str) -> list[Stock]:
        return []

    async def fetch_one(self, code: StockCode) -> Quote | None:
        try:
            pro = self._get_pro()
            df = pro.daily_basic(ts_code=str(code), trade_date=date.today().strftime("%Y%m%d"))
            if df.empty:
                return None
            row = df.iloc[0]
            return Quote(
                code=code,
                name="",
                price=float(row["close"]),
                pe_ttm=float(row["pe_ttm"]) if row.get("pe_ttm") else None,
                pb=float(row["pb"]) if row.get("pb") else None,
                market_cap=float(row["total_mv"]) / 1e4 if row.get("total_mv") else None,
                trade_date=date.today(),
            )
        except Exception:
            return None

    async def fetch_batch(self, codes: list[StockCode]) -> list[Quote]:
        try:
            pro = self._get_pro()
            ts_codes = ",".join(str(c) for c in codes)
            df = pro.daily_basic(ts_code=ts_codes, trade_date=date.today().strftime("%Y%m%d"))
            if df.empty:
                return []
            quotes: list[Quote] = []
            for _, row in df.iterrows():
                code = StockCode(str(row["ts_code"]))
                quotes.append(Quote(
                    code=code,
                    name="",
                    price=float(row["close"]),
                    pe_ttm=float(row["pe_ttm"]) if row.get("pe_ttm") else None,
                    pb=float(row["pb"]) if row.get("pb") else None,
                    market_cap=float(row["total_mv"]) / 1e4 if row.get("total_mv") else None,
                    trade_date=date.today(),
                ))
            return quotes
        except Exception:
            return []

    async def fetch(self, code: StockCode, periods: int = 4) -> list[FinancialReport]:
        return []

    async def fetch_batch(self, codes: list[StockCode], periods: int = 4) -> dict[StockCode, list[FinancialReport]]:
        return {}
```

- [ ] **Step 2: Commit**

```bash
git add backend/src/market/infrastructure/adapters/TushareAdapter.py
git commit -m "feat: add Tushare adapter (activated by account config)"
```

---

## Phase 1 Complete — Verification Checklist

At this point you have a working CLI tool. Verify:

```bash
# Show help
cd backend && python -m src.cli.main --help

# Query a stock quote (free, no LLM needed)
python -m src.cli.main market quote 600001.SH

# If you have a user.yaml with LLM provider configured:
# (copy config/user.yaml.example to config/user.yaml and fill in your key)
python -m src.cli.main screening screen 600001.SH 000001.SZ

# Deep analyze one stock
python -m src.cli.main screening analyze 600001.SH

# Run all tests
python -m pytest tests/ -v
```

**Phase 1 delivers:** CLI tool that queries real A-share market data via AKShare and scores stocks via LLM.

---

## Next Phases (separate plans)

- **Phase 2:** Persistence (SQLite/DuckDB) + FastAPI + User Context → Working Web API
- **Phase 3:** Notification Context (monitoring, IM push, APScheduler) + Event-driven flow
- **Phase 4:** Frontend (React + TypeScript + Ant Design + ECharts)
