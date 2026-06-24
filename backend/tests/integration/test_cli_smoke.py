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
