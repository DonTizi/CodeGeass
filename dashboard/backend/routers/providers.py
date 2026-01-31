"""Provider API router."""

from fastapi import APIRouter, HTTPException

from models.provider import Provider, ProviderSummary, ProviderCapabilities

router = APIRouter(prefix="/api/providers", tags=["providers"])


def _get_registry():
    """Get the provider registry (lazy import to avoid circular imports)."""
    import sys
    from pathlib import Path

    # Add src to path if not already present
    src_path = str(Path(__file__).parent.parent.parent.parent / "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

    from codegeass.providers import get_provider_registry

    return get_provider_registry()


@router.get("", response_model=list[Provider])
async def list_providers():
    """List all registered code execution providers."""
    registry = _get_registry()

    providers = []
    for info in registry.list_provider_info():
        providers.append(
            Provider(
                name=info.name,
                display_name=info.display_name,
                description=info.description,
                capabilities=ProviderCapabilities(
                    plan_mode=info.capabilities.plan_mode,
                    resume=info.capabilities.resume,
                    streaming=info.capabilities.streaming,
                    autonomous=info.capabilities.autonomous,
                    autonomous_flag=info.capabilities.autonomous_flag,
                    models=info.capabilities.models,
                ),
                is_available=info.is_available,
                executable_path=info.executable_path,
            )
        )

    return providers


@router.get("/available", response_model=list[ProviderSummary])
async def list_available_providers():
    """List only available (ready to use) providers."""
    registry = _get_registry()

    providers = []
    for info in registry.list_provider_info():
        if info.is_available:
            providers.append(
                ProviderSummary(
                    name=info.name,
                    display_name=info.display_name,
                    is_available=info.is_available,
                    supports_plan_mode=info.capabilities.plan_mode,
                )
            )

    return providers


@router.get("/{name}", response_model=Provider)
async def get_provider(name: str):
    """Get detailed information about a specific provider."""
    registry = _get_registry()

    try:
        info = registry.get_provider_info(name)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Provider not found: {name}")

    return Provider(
        name=info.name,
        display_name=info.display_name,
        description=info.description,
        capabilities=ProviderCapabilities(
            plan_mode=info.capabilities.plan_mode,
            resume=info.capabilities.resume,
            streaming=info.capabilities.streaming,
            autonomous=info.capabilities.autonomous,
            autonomous_flag=info.capabilities.autonomous_flag,
            models=info.capabilities.models,
        ),
        is_available=info.is_available,
        executable_path=info.executable_path,
    )
