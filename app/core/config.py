from functools import lru_cache
import os
import secrets
from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=True, env_file_encoding="utf-8"
    )

    # App Settings
    APP_NAME: str = "Eventaic"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"  # development, staging, production

    # Security - CRITICAL: Must be set in production .env
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY",
        secrets.token_urlsafe(32),  # Only for dev, MUST override in production
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"
    BCRYPT_ROUNDS: int = 12

    # Security Headers
    ENABLE_SECURITY_HEADERS: bool = True
    ENABLE_HTTPS_REDIRECT: bool = False  # Set True in production

    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/eventaic_db"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 40
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_ECHO: bool = False  # Set to True for SQL debugging

    # CORS - CRITICAL: Update for production
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
    ]
    # For production, use:
    # ALLOWED_ORIGINS: List[str] = ["https://yourdomain.com"]

    # Email Settings
    SMTP_ENABLED: bool = False  # Enable in production
    EMAIL_VERIFICATION_REQUIRED: bool = False  # Enable in production
    SMTP_HOST: Optional[str] = "smtp.gmail.com"
    SMTP_PORT: Optional[int] = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: Optional[str] = "noreply@eventaic.com"
    SMTP_FROM_NAME: Optional[str] = "Eventaic"
    SMTP_USE_TLS: bool = True

    # Dify Settings
    DIFY_API_KEY: str = "app-your-dify-api-key"
    DIFY_BASE_URL: str = "http://agents.algolyzerlab.com/v1"
    DIFY_TIMEOUT: int = 60  # Increased for image generation

    # Redis (optional for caching and rate limiting)
    REDIS_URL: Optional[str] = None
    REDIS_ENABLED: bool = False

    # File Upload
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_IMAGE_TYPES: List[str] = [
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/gif",
    ]
    UPLOAD_DIR: str = "static/images/ads"

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    # Stricter limits for sensitive endpoints
    AUTH_RATE_LIMIT_PER_MINUTE: int = 5
    AUTH_RATE_LIMIT_PER_HOUR: int = 20

    # Frontend URLs
    FRONTEND_URL: str = "http://localhost:3000"
    PASSWORD_RESET_URL: str = "http://localhost:3000/reset-password"
    EMAIL_VERIFY_URL: str = "http://localhost:3000/verify-email"

    # Logging
    LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_FILE: str = "logs/eventaic.log"
    LOG_MAX_BYTES: int = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT: int = 5

    # Session Settings
    SESSION_TIMEOUT_MINUTES: int = 60
    REMEMBER_ME_DAYS: int = 30

    # API Settings
    API_TIMEOUT: int = 30  # seconds
    API_LONG_TIMEOUT: int = 120  # For image generation

    # Monitoring
    SENTRY_DSN: Optional[str] = None
    SENTRY_ENABLED: bool = False

    # Feature Flags
    ENABLE_REGISTRATION: bool = True
    ENABLE_PASSWORD_RESET: bool = True
    ENABLE_EMAIL_VERIFICATION: bool = False
    ENABLE_IMAGE_GENERATION: bool = True

    # Company Limits (default)
    DEFAULT_MONTHLY_AD_LIMIT: int = 100
    MAX_MONTHLY_AD_LIMIT: int = 10000

    # Validation
    MIN_PASSWORD_LENGTH: int = 8
    MAX_PASSWORD_LENGTH: int = 128
    MIN_USERNAME_LENGTH: int = 3
    MAX_USERNAME_LENGTH: int = 50

    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.ENVIRONMENT == "development"

    def validate_production_config(self) -> List[str]:
        """Validate production configuration and return warnings"""
        warnings = []

        if self.is_production:
            # Check SECRET_KEY
            if (
                self.SECRET_KEY == secrets.token_urlsafe(32)
                or len(self.SECRET_KEY) < 32
            ):
                warnings.append(
                    "⚠️ SECRET_KEY must be set to a strong random value in production"
                )

            # Check CORS
            if any(
                origin.startswith("http://localhost") for origin in self.ALLOWED_ORIGINS
            ):
                warnings.append(
                    "⚠️ ALLOWED_ORIGINS contains localhost - update for production"
                )

            # Check HTTPS
            if not self.ENABLE_HTTPS_REDIRECT:
                warnings.append("⚠️ HTTPS redirect should be enabled in production")

            # Check DEBUG
            if self.DEBUG:
                warnings.append("⚠️ DEBUG should be False in production")

            # Check Database
            if "localhost" in self.DATABASE_URL:
                warnings.append(
                    "⚠️ DATABASE_URL points to localhost - use production database"
                )

            # Check Email
            if self.EMAIL_VERIFICATION_REQUIRED and not self.SMTP_ENABLED:
                warnings.append("⚠️ Email verification required but SMTP not enabled")

            # Check Monitoring
            if not self.SENTRY_ENABLED:
                warnings.append("ℹ️ Consider enabling Sentry for error tracking")

        return warnings


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    settings = Settings()

    # Validate production config
    if settings.is_production:
        warnings = settings.validate_production_config()
        if warnings:
            print("\n🚨 PRODUCTION CONFIGURATION WARNINGS:")
            for warning in warnings:
                print(f"  {warning}")
            print("\n")

    return settings


settings = get_settings()

# Export commonly used values
DEBUG = settings.DEBUG
DATABASE_URL = settings.DATABASE_URL
SECRET_KEY = settings.SECRET_KEY
