"""Skills API router."""

from fastapi import APIRouter, HTTPException, Query

from models import Skill, SkillSummary
from dependencies import get_skill_service

router = APIRouter(prefix="/api/skills", tags=["skills"])


@router.get(
    "",
    response_model=list[SkillSummary],
    summary="List all skills",
    description="List all available skills from project and shared skill directories.",
)
async def list_skills():
    """List all available skills.

    Skills are loaded from .claude/skills/ in the project directory
    and ~/.codegeass/skills/ for shared skills.

    Returns:
        List of SkillSummary with name, description, and source location.
    """
    service = get_skill_service()
    return service.list_skills()


@router.get(
    "/{name}",
    response_model=Skill,
    summary="Get a skill by name",
    description="Retrieve full skill details including content, allowed tools, and metadata.",
    responses={404: {"description": "Skill not found"}},
)
async def get_skill(name: str):
    """Get a skill by name.

    Args:
        name: The skill name (e.g., 'commit', 'refactor').

    Returns:
        Full Skill object with content and configuration.

    Raises:
        HTTPException: 404 if skill not found.
    """
    service = get_skill_service()
    skill = service.get_skill(name)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill


@router.post(
    "/reload",
    response_model=list[SkillSummary],
    summary="Reload skills from disk",
    description="Force reload of all skills from disk. Useful after adding or modifying skill files.",
)
async def reload_skills():
    """Reload skills from disk.

    Clears the skill cache and reloads all skills from project
    and shared skill directories.

    Returns:
        Updated list of available skills.
    """
    service = get_skill_service()
    return service.reload_skills()


@router.get(
    "/{name}/preview",
    summary="Preview skill content",
    description="Render a skill with arguments to preview what Claude will receive.",
    responses={404: {"description": "Skill not found"}},
)
async def preview_skill(
    name: str,
    arguments: str = Query("", description="Arguments to pass to the skill (replaces $ARGUMENTS)"),
):
    """Preview skill content with arguments.

    Renders the skill template with provided arguments, showing
    exactly what Claude will receive when the skill is invoked.

    Args:
        name: The skill name.
        arguments: Arguments to substitute for $ARGUMENTS in the skill template.

    Returns:
        Object with name, arguments, and rendered content.

    Raises:
        HTTPException: 404 if skill not found.
    """
    service = get_skill_service()
    content = service.render_skill_content(name, arguments)
    if content is None:
        raise HTTPException(status_code=404, detail="Skill not found")
    return {"name": name, "arguments": arguments, "content": content}
