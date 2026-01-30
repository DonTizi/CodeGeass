"""Configuration for CodeGeass Dashboard backend."""

import os
from pathlib import Path


class Settings:
    """Application settings."""

    # Base paths - use current working directory or env var
    @property
    def PROJECT_DIR(self) -> Path:
        env_dir = os.getenv("CODEGEASS_PROJECT_DIR")
        if env_dir:
            return Path(env_dir)
        return Path.cwd()

    @property
    def CONFIG_DIR(self) -> Path:
        return self.PROJECT_DIR / "config"

    @property
    def DATA_DIR(self) -> Path:
        return self.PROJECT_DIR / "data"

    @property
    def SKILLS_DIR(self) -> Path:
        return self.PROJECT_DIR / ".claude" / "skills"

    # API settings
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://localhost:8001",
        "http://127.0.0.1:8001",
    ]

    # Server settings
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8001"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    def get_schedules_path(self) -> Path:
        return self.CONFIG_DIR / "schedules.yaml"

    def get_logs_dir(self) -> Path:
        return self.DATA_DIR / "logs"

    def get_sessions_dir(self) -> Path:
        return self.DATA_DIR / "sessions"


settings = Settings()
