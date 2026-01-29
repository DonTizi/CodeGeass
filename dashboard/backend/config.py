"""Configuration for CodeGeass Dashboard backend."""

import os
from pathlib import Path


class Settings:
    """Application settings."""

    # Base paths
    PROJECT_DIR: Path = Path(__file__).parent.parent.parent
    CONFIG_DIR: Path = PROJECT_DIR / "config"
    DATA_DIR: Path = PROJECT_DIR / "data"
    SKILLS_DIR: Path = PROJECT_DIR / ".claude" / "skills"

    # API settings
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

    # Server settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8001"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    @classmethod
    def get_schedules_path(cls) -> Path:
        return cls.CONFIG_DIR / "schedules.yaml"

    @classmethod
    def get_logs_dir(cls) -> Path:
        return cls.DATA_DIR / "logs"

    @classmethod
    def get_sessions_dir(cls) -> Path:
        return cls.DATA_DIR / "sessions"


settings = Settings()
