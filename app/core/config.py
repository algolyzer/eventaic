from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List
from functools import lru_cache
import secrets


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

    # App Settings
    APP_NAME: str = "Ad Generation Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_PREFIX: str = "/api/v1"

    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)  # ⚠️ set in .env for stable tokens
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"
    BCRYPT_ROUNDS: int = 12

    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 40
    DATABASE_POOL_TIMEOUT: int = 30

    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]

    # Email Settings
    SMTP_ENABLED: bool = True
    EMAIL_VERIFICATION_REQUIRED: bool = True
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: Optional[str] = None
    SMTP_FROM_NAME: Optional[str] = "Ad Generation Platform"

    # Dify Settings
    DIFY_API_KEY: str
    DIFY_BASE_URL: str = "http://agents.algolyzerlab.com/v1"
    DIFY_TIMEOUT: int = 30

    # Redis (optional for caching)
    REDIS_URL: Optional[str] = None

    # File Upload
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024
    ALLOWED_IMAGE_TYPES: List[str] = ["image/jpeg", "image/png", "image/webp"]

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60

    # Frontend URLs
    FRONTEND_URL: str = "http://localhost:3000"
    PASSWORD_RESET_URL: str = "http://localhost:3000/reset-password"
    EMAIL_VERIFY_URL: str = "http://localhost:3000/verify-email"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
