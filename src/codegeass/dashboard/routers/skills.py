"""Skills API router."""

from fastapi import APIRouter, HTTPException, Query

from ..dependencies import get_skill_service
from ..models import Skill, SkillSummary

router = APIRouter(prefix="/api/skills", tags=["skills"])


@router.get("", response_model=list[SkillSummary])
async def list_skills():
    """List all available skills."""
    service = get_skill_service()
    return service.list_skills()


@router.get("/{name}", response_model=Skill)
async def get_skill(name: str):
    """Get a skill by name."""
    service = get_skill_service()
    skill = service.get_skill(name)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill


@router.post("/reload", response_model=list[SkillSummary])
async def reload_skills():
    """Reload skills from disk."""
    service = get_skill_service()
    return service.reload_skills()


@router.get("/{name}/preview")
async def preview_skill(
    name: str,
    arguments: str = Query("", description="Arguments to pass to the skill"),
):
    """Preview skill content with arguments."""
    service = get_skill_service()
    content = service.render_skill_content(name, arguments)
    if content is None:
        raise HTTPException(status_code=404, detail="Skill not found")
    return {"name": name, "arguments": arguments, "content": content}
