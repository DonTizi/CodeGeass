"""CodeGeass Dashboard FastAPI backend."""

import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime
from importlib.metadata import version as get_version
from pathlib import Path

from fastapi import FastAPI

# Get version from package metadata (single source of truth: pyproject.toml)
try:
    _version = get_version("codegeass")
except Exception:
    _version = "unknown"
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .routers import (
    approvals_router,
    executions_router,
    logs_router,
    notifications_router,
    projects_router,
    scheduler_router,
    skills_router,
    tasks_router,
)

# Static files directory
STATIC_DIR = Path(__file__).parent / "static"

# Global reference to callback server task
_callback_server_task: asyncio.Task | None = None
# Global reference to execution broadcast task
_execution_broadcast_task: asyncio.Task | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    global _callback_server_task, _execution_broadcast_task

    # Initialize services on startup
    from .dependencies import (
        get_approval_repo,
        get_channel_repo,
        get_log_repo,
        get_scheduler,
        get_skill_registry,
        get_task_repo,
    )

    # Warm up singletons
    get_task_repo()
    get_log_repo()
    get_skill_registry()
    get_scheduler()

    # Clean up stale executions
    try:
        from codegeass.execution.tracker import get_execution_tracker

        approval_repo = get_approval_repo()
        tracker = get_execution_tracker()

        pending_approvals = approval_repo.list_pending()
        valid_ids = {a.id for a in pending_approvals}
        removed = tracker.cleanup_stale_executions(valid_ids)
        if removed > 0:
            print(f"[Startup] Cleaned up {removed} stale execution(s)")
    except Exception as e:
        print(f"[Startup] Warning: Could not clean stale executions: {e}")

    # Start execution broadcast loop
    try:
        from .services.execution_service import get_execution_manager

        execution_manager = get_execution_manager()
        _execution_broadcast_task = asyncio.create_task(execution_manager.broadcast_loop())
        print("[Execution Monitor] Real-time monitoring started")
    except Exception as e:
        print(f"[Execution Monitor] Warning: Could not start: {e}")

    # Start Telegram callback server
    try:
        from codegeass.execution.plan_service import PlanApprovalService
        from codegeass.notifications.callback_handler import (
            get_callback_handler,
            get_callback_server,
        )

        channel_repo = get_channel_repo()
        approval_repo = get_approval_repo()

        plan_service = PlanApprovalService(approval_repo, channel_repo)
        callback_handler = get_callback_handler(plan_service, channel_repo)
        callback_server = get_callback_server(callback_handler, channel_repo)

        _callback_server_task = asyncio.create_task(callback_server.start())
        print("[Callback Server] Telegram callback server started")

    except Exception as e:
        print(f"[Callback Server] Warning: Could not start: {e}")

    yield

    # Cleanup on shutdown
    if _execution_broadcast_task:
        try:
            from .services.execution_service import get_execution_manager

            execution_manager = get_execution_manager()
            execution_manager.stop()
            _execution_broadcast_task.cancel()
            try:
                await _execution_broadcast_task
            except asyncio.CancelledError:
                pass
        except Exception:
            pass

    if _callback_server_task:
        try:
            from codegeass.notifications.callback_handler import reset_callback_server

            reset_callback_server()
            _callback_server_task.cancel()
            try:
                await _callback_server_task
            except asyncio.CancelledError:
                pass
        except Exception:
            pass


app = FastAPI(
    title="CodeGeass Dashboard API",
    description="API for managing CodeGeass scheduled tasks",
    version=_version,
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
app.include_router(approvals_router)
app.include_router(executions_router)
app.include_router(projects_router)


# Health check
@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


# CRON validation endpoint
@app.post("/api/cron/validate")
async def validate_cron(body: dict) -> dict:
    """Validate a CRON expression."""
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


# Serve static frontend files
if STATIC_DIR.exists():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve the SPA for all non-API routes."""
        # Check if it's an API route
        if full_path.startswith("api/") or full_path in ["health", "ws"]:
            return {"error": "Not found"}

        # Serve index.html for SPA routing
        index_file = STATIC_DIR / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return {"error": "Frontend not found"}


def run_server(host: str = "127.0.0.1", port: int = 8001):
    """Run the dashboard server."""
    import uvicorn

    print("\n  CodeGeass Dashboard")
    print(f"  http://{host}:{port}\n")

    uvicorn.run(
        "codegeass.dashboard.main:app",
        host=host,
        port=port,
        reload=False,
    )


if __name__ == "__main__":
    run_server()
