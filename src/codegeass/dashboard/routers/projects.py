"""Project API router - thin wrapper around CLI library.

This router imports directly from the CLI library (src/codegeass/)
following the "CLI is the source of truth" architecture principle.
"""

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from codegeass.core.entities import Project as ProjectEntity
from codegeass.factory.skill_resolver import ChainedSkillRegistry
from codegeass.scheduling.cron_parser import CronParser
from codegeass.storage.project_repository import ProjectRepository
from codegeass.storage.task_repository import TaskRepository

from ..models.project import (
    Project,
    ProjectCreate,
    ProjectUpdate,
    SkillWithSource,
    TaskWithProject,
)

router = APIRouter(prefix="/api/projects", tags=["projects"])

# Singleton instance
_project_repo: ProjectRepository | None = None


def get_project_repo() -> ProjectRepository:
    """Get or create ProjectRepository singleton."""
    global _project_repo
    if _project_repo is None:
        _project_repo = ProjectRepository()
    return _project_repo


def _project_to_response(project: ProjectEntity, default_id: str | None = None) -> Project:
    """Convert CLI Project entity to API response model."""
    # Count skills
    skill_count = 0
    if project.skills_dir.exists():
        skill_count = len([
            d for d in project.skills_dir.iterdir()
            if d.is_dir() and (d / "SKILL.md").exists()
        ])

    # Count tasks
    task_count = 0
    if project.schedules_file.exists():
        try:
            task_repo = TaskRepository(project.schedules_file)
            task_count = len(task_repo.find_all())
        except Exception:
            pass

    return Project(
        id=project.id,
        name=project.name,
        path=str(project.path),
        description=project.description,
        default_model=project.default_model,
        default_timeout=project.default_timeout,
        default_autonomous=project.default_autonomous,
        git_remote=project.git_remote,
        enabled=project.enabled,
        use_shared_skills=project.use_shared_skills,
        created_at=project.created_at,
        task_count=task_count,
        skill_count=skill_count,
        is_default=project.id == default_id if default_id else False,
        exists=project.exists(),
        is_initialized=project.is_initialized(),
    )


@router.get("", response_model=list[Project])
async def list_projects(
    enabled_only: bool = Query(False, description="Only return enabled projects"),
) -> list[Project]:
    """List all registered projects."""
    repo = get_project_repo()
    default_id = repo.get_default_project_id()

    if enabled_only:
        projects = repo.find_enabled()
    else:
        projects = repo.find_all()

    return [_project_to_response(p, default_id) for p in projects]


@router.get("/tasks/all", response_model=list[TaskWithProject])
async def get_all_tasks(
    enabled_only: bool = Query(False, description="Only return tasks from enabled projects"),
    project_enabled_only: bool = Query(True, description="Only include enabled tasks"),
) -> list[TaskWithProject]:
    """Get aggregated tasks from all projects."""
    repo = get_project_repo()

    if enabled_only:
        projects = repo.find_enabled()
    else:
        projects = repo.find_all()

    all_tasks: list[TaskWithProject] = []

    for project in projects:
        if not project.schedules_file.exists():
            continue

        try:
            task_repo = TaskRepository(project.schedules_file)
            tasks = task_repo.find_all()

            for task in tasks:
                if project_enabled_only and not task.enabled:
                    continue

                # Get next run and description
                next_run = None
                schedule_desc = None
                try:
                    next_run = CronParser.get_next(task.schedule).isoformat()
                    schedule_desc = CronParser.describe(task.schedule)
                except Exception:
                    pass

                all_tasks.append(TaskWithProject(
                    id=task.id,
                    name=task.name,
                    schedule=task.schedule,
                    working_dir=str(task.working_dir),
                    skill=task.skill,
                    prompt=task.prompt,
                    model=task.model,
                    autonomous=task.autonomous,
                    timeout=task.timeout,
                    enabled=task.enabled,
                    last_run=task.last_run,
                    last_status=task.last_status,
                    next_run=next_run,
                    schedule_description=schedule_desc,
                    project_id=project.id,
                    project_name=project.name,
                ))
        except Exception:
            pass

    return all_tasks


@router.get("/{project_id}", response_model=Project)
async def get_project(project_id: str) -> Project:
    """Get a project by ID or name."""
    repo = get_project_repo()
    project = repo.find_by_id_or_name(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    default_id = repo.get_default_project_id()
    return _project_to_response(project, default_id)


@router.post("", response_model=Project, status_code=201)
async def add_project(data: ProjectCreate) -> Project:
    """Register a new project."""
    repo = get_project_repo()

    path = Path(data.path).resolve()

    # Check if path exists
    if not path.exists():
        raise HTTPException(status_code=400, detail=f"Path does not exist: {path}")

    # Check if already registered
    existing = repo.find_by_path(path)
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Project already registered: {existing.name} ({existing.id})"
        )

    # Check for name collision
    project_name = data.name or path.name
    existing_name = repo.find_by_name(project_name)
    if existing_name:
        raise HTTPException(
            status_code=400,
            detail=f"Project with name '{project_name}' already exists"
        )

    # Try to get git remote
    git_remote = None
    git_config = path / ".git" / "config"
    if git_config.exists():
        try:
            import configparser
            config = configparser.ConfigParser()
            config.read(git_config)
            if 'remote "origin"' in config:
                git_remote = config['remote "origin"'].get("url")
        except Exception:
            pass

    # Create project
    new_project = ProjectEntity.create(
        name=project_name,
        path=path,
        description=data.description,
        default_model=data.default_model,
        default_timeout=data.default_timeout,
        default_autonomous=data.default_autonomous,
        git_remote=git_remote,
        use_shared_skills=data.use_shared_skills,
    )

    repo.save(new_project)

    # Set as default if first project
    if len(repo.find_all()) == 1:
        repo.set_default_project(new_project.id)

    default_id = repo.get_default_project_id()
    return _project_to_response(new_project, default_id)


@router.put("/{project_id}", response_model=Project)
async def update_project(project_id: str, data: ProjectUpdate) -> Project:
    """Update a project's configuration."""
    repo = get_project_repo()
    project = repo.find_by_id_or_name(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check for name collision if renaming
    if data.name and data.name.lower() != project.name.lower():
        existing = repo.find_by_name(data.name)
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Project with name '{data.name}' already exists"
            )

    # Update fields
    if data.name is not None:
        project.name = data.name
    if data.description is not None:
        project.description = data.description
    if data.default_model is not None:
        project.default_model = data.default_model
    if data.default_timeout is not None:
        project.default_timeout = data.default_timeout
    if data.default_autonomous is not None:
        project.default_autonomous = data.default_autonomous
    if data.use_shared_skills is not None:
        project.use_shared_skills = data.use_shared_skills
    if data.enabled is not None:
        project.enabled = data.enabled

    repo.save(project)

    default_id = repo.get_default_project_id()
    return _project_to_response(project, default_id)


@router.delete("/{project_id}")
async def remove_project(project_id: str) -> dict:
    """Unregister a project.

    This only removes the project from the registry.
    Project files are not deleted.
    """
    repo = get_project_repo()
    project = repo.find_by_id_or_name(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    repo.delete(project.id)
    return {"status": "success", "message": f"Project {project.name} unregistered"}


@router.post("/{project_id}/set-default")
async def set_default_project(project_id: str) -> dict:
    """Set a project as the default."""
    repo = get_project_repo()
    project = repo.find_by_id_or_name(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    repo.set_default_project(project.id)
    return {"status": "success", "message": f"Default project set to {project.name}"}


@router.post("/{project_id}/enable")
async def enable_project(project_id: str) -> dict:
    """Enable a project."""
    repo = get_project_repo()

    if not repo.enable(project_id):
        raise HTTPException(status_code=404, detail="Project not found")

    return {"status": "success", "message": "Project enabled"}


@router.post("/{project_id}/disable")
async def disable_project(project_id: str) -> dict:
    """Disable a project."""
    repo = get_project_repo()

    if not repo.disable(project_id):
        raise HTTPException(status_code=404, detail="Project not found")

    return {"status": "success", "message": "Project disabled"}


@router.get("/{project_id}/tasks", response_model=list[TaskWithProject])
async def get_project_tasks(
    project_id: str,
    enabled_only: bool = Query(False, description="Only return enabled tasks"),
) -> list[TaskWithProject]:
    """Get tasks for a specific project."""
    repo = get_project_repo()
    project = repo.find_by_id_or_name(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not project.schedules_file.exists():
        return []

    task_repo = TaskRepository(project.schedules_file)

    if enabled_only:
        tasks = task_repo.find_enabled()
    else:
        tasks = task_repo.find_all()

    result: list[TaskWithProject] = []
    for task in tasks:
        # Get next run and description
        next_run = None
        schedule_desc = None
        try:
            next_run = CronParser.get_next(task.schedule).isoformat()
            schedule_desc = CronParser.describe(task.schedule)
        except Exception:
            pass

        result.append(TaskWithProject(
            id=task.id,
            name=task.name,
            schedule=task.schedule,
            working_dir=str(task.working_dir),
            skill=task.skill,
            prompt=task.prompt,
            model=task.model,
            autonomous=task.autonomous,
            timeout=task.timeout,
            enabled=task.enabled,
            last_run=task.last_run,
            last_status=task.last_status,
            next_run=next_run,
            schedule_description=schedule_desc,
            project_id=project.id,
            project_name=project.name,
        ))

    return result


@router.get("/{project_id}/skills", response_model=list[SkillWithSource])
async def get_project_skills(project_id: str) -> list[SkillWithSource]:
    """Get skills for a specific project.

    Returns project-specific skills first, then shared skills (if enabled).
    """
    repo = get_project_repo()
    project = repo.find_by_id_or_name(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Use ChainedSkillRegistry
    registry = ChainedSkillRegistry(
        project_skills_dir=project.skills_dir,
        shared_skills_dir=repo.get_shared_skills_dir(),
        use_shared=project.use_shared_skills,
    )

    result: list[SkillWithSource] = []
    for skill, source in registry.get_all_with_source():
        result.append(SkillWithSource(
            name=skill.name,
            description=skill.description,
            source=source,
            path=str(skill.path),
            allowed_tools=skill.allowed_tools,
            context=skill.context,
            agent=skill.agent,
        ))

    return result


@router.get("/default")
async def get_default_project() -> Project | None:
    """Get the default project."""
    repo = get_project_repo()
    project = repo.get_default_project()

    if not project:
        return None

    default_id = repo.get_default_project_id()
    return _project_to_response(project, default_id)
