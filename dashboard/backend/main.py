"""CodeGeass Dashboard FastAPI backend."""

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from routers import (
    tasks_router,
    skills_router,
    logs_router,
    scheduler_router,
    notifications_router,
    approvals_router,
    executions_router,
    projects_router,
    filesystem_router,
)

# Global reference to callback server task
_callback_server_task: asyncio.Task | None = None
# Global reference to execution broadcast task
_execution_broadcast_task: asyncio.Task | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    global _callback_server_task, _execution_broadcast_task

    # Initialize services on startup
    from dependencies import (
        get_task_repo,
        get_log_repo,
        get_skill_registry,
        get_scheduler,
        get_channel_repo,
        get_approval_repo,
    )

    # Warm up singletons
    get_task_repo()
    get_log_repo()
    get_skill_registry()
    get_scheduler()

    # Clean up stale executions (waiting_approval with expired/cancelled approvals)
    try:
        from codegeass.execution.tracker import get_execution_tracker

        approval_repo = get_approval_repo()
        tracker = get_execution_tracker()

        # Get all pending approval IDs
        pending_approvals = approval_repo.list_pending()
        valid_ids = {a.id for a in pending_approvals}

        # Clean up executions waiting for approvals that no longer exist
        removed = tracker.cleanup_stale_executions(valid_ids)
        if removed > 0:
            print(f"[Startup] Cleaned up {removed} stale execution(s)")
    except Exception as e:
        print(f"[Startup] Warning: Could not clean stale executions: {e}")

    # Start execution broadcast loop for real-time monitoring
    try:
        from services.execution_service import get_execution_manager

        execution_manager = get_execution_manager()
        _execution_broadcast_task = asyncio.create_task(execution_manager.broadcast_loop())
        print("[Execution Monitor] Real-time monitoring started")
    except Exception as e:
        print(f"[Execution Monitor] Warning: Could not start execution monitoring: {e}")
        import traceback
        traceback.print_exc()

    # Start Telegram callback server for plan mode buttons
    try:
        from codegeass.notifications.callback_handler import (
            get_callback_handler,
            get_callback_server,
        )
        from codegeass.execution.plan_service import PlanApprovalService

        channel_repo = get_channel_repo()
        approval_repo = get_approval_repo()

        # Create plan service for callback handler
        plan_service = PlanApprovalService(approval_repo, channel_repo)

        # Create callback handler and server
        callback_handler = get_callback_handler(plan_service, channel_repo)
        callback_server = get_callback_server(callback_handler, channel_repo)

        # Start the polling server as a background task
        _callback_server_task = asyncio.create_task(callback_server.start())
        print("[Callback Server] Telegram callback server started")

    except Exception as e:
        print(f"[Callback Server] Warning: Could not start callback server: {e}")
        import traceback
        traceback.print_exc()

    yield

    # Cleanup on shutdown
    if _execution_broadcast_task:
        try:
            from services.execution_service import get_execution_manager
            execution_manager = get_execution_manager()
            execution_manager.stop()
            _execution_broadcast_task.cancel()
            try:
                await _execution_broadcast_task
            except asyncio.CancelledError:
                pass
            print("[Execution Monitor] Real-time monitoring stopped")
        except Exception as e:
            print(f"[Execution Monitor] Error stopping execution monitoring: {e}")

    if _callback_server_task:
        try:
            from codegeass.notifications.callback_handler import reset_callback_server
            reset_callback_server()
            _callback_server_task.cancel()
            try:
                await _callback_server_task
            except asyncio.CancelledError:
                pass
            print("[Callback Server] Telegram callback server stopped")
        except Exception as e:
            print(f"[Callback Server] Error stopping callback server: {e}")


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
app.include_router(approvals_router)
app.include_router(executions_router)
app.include_router(projects_router)
app.include_router(filesystem_router)


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
    sys.path.insert(0, str(settings.project_dir / "src"))
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
