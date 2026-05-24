import warnings

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # abaikan variabel .env yang tidak dikenal
    )

    # ── Database ──────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/sicure_db"

    # ── JWT ───────────────────────────────────────────────────────
    # Mendukung nama variabel dari DeployCC (SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES)
    # maupun nama asli (JWT_SECRET, JWT_ALGORITHM, JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    JWT_SECRET: str = "change-me"
    SECRET_KEY: str = ""  # fallback dari DeployCC
    JWT_REFRESH_SECRET: str = "change-me-refresh"
    JWT_ALGORITHM: str = "HS256"
    ALGORITHM: str = ""  # fallback dari DeployCC
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30       # access token: 30 menit
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 0  # fallback dari DeployCC
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7          # refresh token: 7 hari

    # ── CORS ──────────────────────────────────────────────────────
    ALLOWED_ORIGINS: str = "http://localhost:5173"

    # ── File Upload ───────────────────────────────────────────────
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 5  # per-file limit in megabytes

    # ── Environment ───────────────────────────────────────────────
    APP_ENV: str = "development"  # "development" | "production"
    ENVIRONMENT: str = ""  # fallback dari DeployCC

    @model_validator(mode="after")
    def _resolve_deploycc_aliases(self) -> "Settings":
        """
        Resolve nama variabel dari DeployCC ke nama yang dipakai aplikasi.
        DeployCC generate: SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, ENVIRONMENT
        Aplikasi pakai: JWT_SECRET, JWT_ALGORITHM, JWT_ACCESS_TOKEN_EXPIRE_MINUTES, APP_ENV
        """
        # DATABASE_URL: pastikan pakai asyncpg driver
        if self.DATABASE_URL.startswith("postgresql://"):
            self.DATABASE_URL = self.DATABASE_URL.replace(
                "postgresql://", "postgresql+asyncpg://", 1
            )

        # JWT_SECRET ← SECRET_KEY (jika JWT_SECRET masih default)
        if self.SECRET_KEY and self.JWT_SECRET == "change-me":
            self.JWT_SECRET = self.SECRET_KEY

        # JWT_REFRESH_SECRET ← SECRET_KEY + suffix (jika belum di-set)
        if self.SECRET_KEY and self.JWT_REFRESH_SECRET == "change-me-refresh":
            self.JWT_REFRESH_SECRET = self.SECRET_KEY + "-refresh"

        # JWT_ALGORITHM ← ALGORITHM
        if self.ALGORITHM and self.JWT_ALGORITHM == "HS256":
            self.JWT_ALGORITHM = self.ALGORITHM

        # JWT_ACCESS_TOKEN_EXPIRE_MINUTES ← ACCESS_TOKEN_EXPIRE_MINUTES
        if self.ACCESS_TOKEN_EXPIRE_MINUTES > 0 and self.JWT_ACCESS_TOKEN_EXPIRE_MINUTES == 30:
            self.JWT_ACCESS_TOKEN_EXPIRE_MINUTES = self.ACCESS_TOKEN_EXPIRE_MINUTES

        # APP_ENV ← ENVIRONMENT
        if self.ENVIRONMENT and self.APP_ENV == "development":
            self.APP_ENV = self.ENVIRONMENT

        return self

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
