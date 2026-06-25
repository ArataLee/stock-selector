import os
import yaml
from pathlib import Path
from fastapi import APIRouter, HTTPException
from src.api.schemas.config_dto import ProviderConfigRequest, DataSourceAccountRequest
from src.api.deps import _cached_bootstrap, _clear_bootstrap_cache
from src.llm.domain.ModelProvider import ProviderConfig

router = APIRouter(prefix="/api/config", tags=["config"])

CONFIG_DIR = Path(__file__).parent.parent.parent.parent / "config"
DEFAULT_CONFIG_PATH = CONFIG_DIR / "default.yaml"


def _read_config() -> dict:
    with open(DEFAULT_CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _write_config(config: dict) -> None:
    with open(DEFAULT_CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)


@router.get("/llm-providers")
async def list_providers():
    ctx = _cached_bootstrap()
    providers = ctx.provider_registry.providers
    return {
        "providers": [
            {"id": p.id, "api_base": p.api_base, "model": p.model, "default": p.default}
            for p in providers
        ]
    }


@router.put("/llm-providers/{provider_id}")
async def upsert_provider(provider_id: str, req: ProviderConfigRequest):
    ctx = _cached_bootstrap()
    cfg = ProviderConfig(
        id=req.id,
        api_base=req.api_base,
        api_key=req.api_key,
        model=req.model,
        default=req.default,
        max_tokens=req.max_tokens,
    )
    ctx.provider_registry.add(cfg)

    # Persist to default.yaml
    config = _read_config()
    if "llm" not in config:
        config["llm"] = {}
    providers = config["llm"].get("providers", [])
    providers = [p for p in providers if p.get("id") != provider_id]
    providers.append({
        "id": req.id,
        "api_base": req.api_base,
        "api_key": req.api_key,
        "model": req.model,
        "default": req.default,
        "max_tokens": req.max_tokens,
    })
    config["llm"]["providers"] = providers
    _write_config(config)

    _clear_bootstrap_cache()
    return {"status": "configured", "provider_id": provider_id}


@router.get("/data-sources")
async def list_data_sources():
    ctx = _cached_bootstrap()
    return {
        "sources": [
            {"id": s.id, "name": s.name, "type": s.type.value, "priority": s.priority, "enabled": s.enabled}
            for s in ctx.data_source_registry.sources
        ]
    }


@router.put("/data-sources/{source_id}/account")
async def set_data_source_account(source_id: str, req: DataSourceAccountRequest):
    ctx = _cached_bootstrap()
    ctx.data_source_registry.enable(source_id)

    # Persist to default.yaml
    config = _read_config()
    if "market" not in config:
        config["market"] = {}
    if "accounts" not in config["market"]:
        config["market"]["accounts"] = {}
    config["market"]["accounts"][source_id] = {"token": req.token}
    _write_config(config)

    _clear_bootstrap_cache()
    return {"status": "configured", "source_id": source_id}


@router.delete("/data-sources/{source_id}/account")
async def remove_data_source_account(source_id: str):
    ctx = _cached_bootstrap()
    ctx.data_source_registry.disable(source_id)

    config = _read_config()
    if "market" in config and "accounts" in config["market"]:
        config["market"]["accounts"].pop(source_id, None)
        _write_config(config)

    _clear_bootstrap_cache()
    return {"status": "removed", "source_id": source_id}


@router.get("/prompts")
async def list_prompts():
    from src.llm.domain.Prompt import BUILTIN_PROMPTS
    return {
        "prompts": [
            {"id": pid, "scenario": p.scenario, "description": p.description}
            for pid, p in BUILTIN_PROMPTS.items()
        ]
    }
