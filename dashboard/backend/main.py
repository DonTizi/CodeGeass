"""CodeGeass Dashboard FastAPI backend."""

from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from routers import tasks_router, skills_router, logs_router, scheduler_router, notifications_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    # Initialize services on startup
    from dependencies import (
        get_task_repo,
        get_log_repo,
        get_skill_registry,
        get_scheduler,
    )

    # Warm up singletons
    get_task_repo()
    get_log_repo()
    get_skill_registry()
    get_scheduler()

    yield

    # Cleanup on shutdown (if needed)


app = FastAPI(
    title="CodeGeass Dashboard API",
    description="API for managing CodeGeass scheduled tasks",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(tasks_router)
app.include_router(skills_router)
app.include_router(logs_router)
app.include_router(scheduler_router)
app.include_router(notifications_router)


# Health check
@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


# CRON validation endpoint
@app.post("/api/cron/validate")
async def validate_cron(body: dict) -> dict:
    """Validate a CRON expression."""
    import sys
    sys.path.insert(0, str(settings.PROJECT_DIR / "src"))
    from codegeass.scheduling.cron_parser import CronParser

    expression = body.get("expression", "")

    if not expression:
        return {"valid": False, "error": "Expression is required"}

    if not CronParser.validate(expression):
        return {"valid": False, "error": "Invalid CRON expression"}

    try:
        next_runs = CronParser.get_next_n(expression, 5)
        description = CronParser.describe(expression)
        return {
            "valid": True,
            "description": description,
            "next_runs": [r.isoformat() for r in next_runs],
        }
    except Exception as e:
        return {"valid": False, "error": str(e)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
