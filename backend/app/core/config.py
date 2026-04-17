import warnings

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # ── Database ──────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/sicure_db"

    # ── JWT ───────────────────────────────────────────────────────
    JWT_SECRET: str = "change-me"
    JWT_REFRESH_SECRET: str = "change-me-refresh"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30       # access token: 30 menit
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7          # refresh token: 7 hari

    # ── CORS ──────────────────────────────────────────────────────
    ALLOWED_ORIGINS: str = "http://localhost:5173"

    # ── File Upload ───────────────────────────────────────────────
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 5  # per-file limit in megabytes

    # ── Environment ───────────────────────────────────────────────
    APP_ENV: str = "development"  # "development" | "production"

    def model_post_init(self, __context) -> None:
        """Warn if JWT secrets are still using placeholder values."""
        _weak_secrets = {
            "change-me",
            "change-me-refresh",
            "your-secret-key-here",
            "your-refresh-secret-key-here",
            "your-secret-key-change-me-in-production",
            "your-refresh-secret-change-me-in-production",
        }
        if self.JWT_SECRET in _weak_secrets:
            warnings.warn(
                "JWT_SECRET masih menggunakan nilai default! "
                'Generate secret baru: python -c "import secrets; print(secrets.token_urlsafe(64))"',
                stacklevel=2,
            )
        if self.JWT_REFRESH_SECRET in _weak_secrets:
            warnings.warn(
                "JWT_REFRESH_SECRET masih menggunakan nilai default! "
                'Generate secret baru: python -c "import secrets; print(secrets.token_urlsafe(64))"',
                stacklevel=2,
            )

    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    @property
    def is_production(self) -> bool:
        return self.APP_ENV.lower() == "production"

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024


settings = Settings()
