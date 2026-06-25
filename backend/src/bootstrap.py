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
from src.screening.application.DiscoveryService import DiscoveryService


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
        self.discovery_service: DiscoveryService | None = None


def load_config(config_dir: str) -> dict:
    """Load config: user.yaml deep-merges over default.yaml"""
    base = Path(config_dir)

    default_path = base / "default.yaml"
    if not default_path.exists():
        raise FileNotFoundError(f"Default config not found: {default_path}")
    with open(default_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

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

    # Check user account config, auto-enable account-type data sources
    accounts = market_cfg.get("accounts", {})
    akshare = AKShareAdapter()
    adapters = [akshare]

    if "tushare" in accounts:
        try:
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

    ctx.discovery_service = DiscoveryService(
        quote_repo=ctx.quote_router,
        financial_repo=ctx.financial_router,
        llm_adapter=ctx.llm_adapter,
        screen_usecase=ctx.screen_usecase,
    )

    return ctx
