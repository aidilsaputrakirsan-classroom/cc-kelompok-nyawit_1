from typing import Any

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Database ──────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/sicure_db"

    # ── JWT ───────────────────────────────────────────────────────
    JWT_SECRET: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_HOURS: int = 8

    # ── CORS ──────────────────────────────────────────────────────
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # ── File Upload ───────────────────────────────────────────────
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 5  # per-file limit in megabytes

    # ── Environment ───────────────────────────────────────────────
    APP_ENV: str = "development"  # "development" | "production"
    LOG_LEVEL: str = "DEBUG"

    @model_validator(mode="before")
    @classmethod
    def apply_railway_aliases(cls, data: Any) -> Any:
        """Map Railway / modul-11 env var names ke field aplikasi."""
        if not isinstance(data, dict):
            return data

        aliases = {
            "CORS_ORIGINS": "ALLOWED_ORIGINS",
            "SECRET_KEY": "JWT_SECRET",
            "ENVIRONMENT": "APP_ENV",
        }
        for src, dst in aliases.items():
            if src in data and dst not in data:
                data[dst] = data[src]

        return data

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        """Railway memberi postgresql:// — SQLAlchemy async butuh asyncpg driver."""
        if isinstance(value, str) and value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+asyncpg://", 1)
        return value

    @model_validator(mode="after")
    def set_log_level_for_environment(self) -> "Settings":
        if self.APP_ENV.lower() == "production" and self.LOG_LEVEL == "DEBUG":
            object.__setattr__(self, "LOG_LEVEL", "INFO")
        return self

    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.APP_ENV.lower() == "production"

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024


settings = Settings()
