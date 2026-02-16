"""Hooks API router."""

from fastapi import APIRouter, HTTPException

from ..dependencies import get_hook_service
from ..models.hook import (
    Hook,
    HookCreate,
    HookPreview,
    HookSummary,
    HookUpdate,
    HookValidation,
)

router = APIRouter(prefix="/api/hooks", tags=["hooks"])


@router.get("", response_model=list[HookSummary])
async def list_hooks():
    """List all hook tags."""
    service = get_hook_service()
    return service.list_tags()


@router.get("/templates", response_model=list[str])
async def list_templates():
    """List available built-in templates."""
    service = get_hook_service()
    return service.get_templates()


@router.post("/init", response_model=list[str])
async def init_templates(overwrite: bool = False):
    """Initialize hooks from built-in templates."""
    service = get_hook_service()
    return service.init_templates(overwrite=overwrite)


@router.get("/{tag}", response_model=Hook)
async def get_hook(tag: str):
    """Get a hook by tag name."""
    service = get_hook_service()
    hook = service.get_tag(tag)
    if not hook:
        raise HTTPException(status_code=404, detail=f"Hook not found: {tag}")
    return hook


@router.post("", response_model=Hook)
async def create_hook(data: HookCreate):
    """Create a new hook tag."""
    service = get_hook_service()

    if service.exists(data.tag):
        raise HTTPException(status_code=409, detail=f"Hook already exists: {data.tag}")

    try:
        return service.create_tag(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{tag}", response_model=Hook)
async def update_hook(tag: str, data: HookUpdate):
    """Update an existing hook tag."""
    service = get_hook_service()

    hook = service.update_tag(tag, data)
    if not hook:
        raise HTTPException(status_code=404, detail=f"Hook not found: {tag}")

    return hook


@router.delete("/{tag}")
async def delete_hook(tag: str):
    """Delete a hook tag."""
    service = get_hook_service()

    if not service.delete_tag(tag):
        raise HTTPException(status_code=404, detail=f"Hook not found: {tag}")

    return {"status": "success", "message": f"Hook deleted: {tag}"}


@router.get("/{tag}/validate", response_model=HookValidation)
async def validate_hook(tag: str):
    """Validate a hook tag configuration."""
    service = get_hook_service()
    return service.validate_tag(tag)


@router.post("/preview", response_model=HookPreview)
async def preview_hooks(tags: list[str]):
    """Preview merged hooks for given tags."""
    service = get_hook_service()

    if not tags:
        raise HTTPException(status_code=400, detail="At least one tag is required")

    return service.preview_tags(tags)
