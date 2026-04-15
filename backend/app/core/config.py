from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/sicure_db"
    JWT_SECRET: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_HOURS: int = 8
    ALLOWED_ORIGINS: str = "http://localhost:5173"
    UPLOAD_DIR: str = "./uploads"

    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]


settings = Settings()
