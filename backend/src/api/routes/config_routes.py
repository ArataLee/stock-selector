from fastapi import APIRouter, HTTPException
from src.api.schemas.config_dto import ProviderConfigRequest, DataSourceAccountRequest
from src.api.deps import _cached_bootstrap
from src.llm.domain.ModelProvider import ProviderConfig

router = APIRouter(prefix="/api/config", tags=["config"])


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
    return {"status": "configured", "source_id": source_id}


@router.delete("/data-sources/{source_id}/account")
async def remove_data_source_account(source_id: str):
    ctx = _cached_bootstrap()
    ctx.data_source_registry.disable(source_id)
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
