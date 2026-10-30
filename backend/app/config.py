"""Configuration management module for the Network Complaint Portal backend.

This module reads application settings from environment variables using
Pydantic Settings, providing type verification and default values for local development.

Key Configurations:
- Database connection (MongoDB URI and database name)
- Staff authentication & JWT security
- Multi-provider LLM & Vector Store settings
- Complaint Management (Part 2) OTP, email, auto-close, and scoring settings
"""

import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or defaults."""

    # General Application Settings
    APP_ENV: str = "development"
    COLLEGE_NAME: str = "MNNIT Allahabad"
    FRONTEND_ORIGIN: str = "http://localhost:5173"
    PUBLIC_BASE_URL: str = "http://localhost:5173"
    APP_TIMEZONE: str = "Asia/Kolkata"

    # MongoDB Settings
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "network_portal"

    # Authentication & JWT Security
    JWT_SECRET: str = "mnnit-network-portal-jwt-secret-key-32bytes-min"
    JWT_EXPIRE_HOURS: int = 8
    LOGIN_MAX_FAILURES: int = 5
    LOGIN_LOCK_MINUTES: int = 15

    # OTP Registration Settings
    ALLOWED_EMAIL_DOMAIN: str = "mnnit.ac.in"
    OTP_SECRET: str = "mnnit-otp-secret-key-32bytes-min"
    OTP_EXPIRE_MINUTES: int = 10
    OTP_MAX_ATTEMPTS: int = 5
    OTP_RESEND_SECONDS: int = 60
    OTP_MAX_RESENDS: int = 3
    OTP_MAX_REQUESTS_PER_EMAIL_PER_HOUR: int = 5

    # Lifecycle & Confirmation Token Settings
    AUTO_CLOSE_DAYS: int = 3
    AUTO_CLOSE_CHECK_MINUTES: int = 30
    ACTION_TOKEN_EXPIRY_DAYS: int = 14

    # Email & SMTP Settings
    EMAIL_BACKEND: str = "console"  # console | smtp
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 25
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_USE_TLS: bool = False
    EMAIL_FROM: str = "noreply@mnnit.ac.in"
    INCHARGE_CC_EMAILS: str = ""

    # Leaderboard Scoring Settings
    SCORE_FORMULA: str = "average"  # average | weighted
    SCORE_PRIOR_MEAN: float = 3.5
    SCORE_PRIOR_COUNT: float = 5.0

    # Multi-Provider LLM Fallback Configuration
    LLM_PROVIDER_ORDER: str = "gemini,openai,grok,anthropic,mock"

    # Provider API Keys
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    GROK_API_KEY: str = ""
    LLM_API_KEY: str = ""  # Anthropic API Key

    # Provider Models
    GEMINI_MODEL: str = "gemini-1.5-flash"
    GEMINI_TIMEOUT: float = 60.0  # Configurable Gemini timeout in seconds (default 60s)
    OPENAI_MODEL: str = "gpt-4o-mini"
    GROK_MODEL: str = "grok-beta"
    LLM_MODEL_CHAT: str = "claude-3-5-sonnet-20241022"
    LLM_MODEL_GUARD: str = "claude-3-5-haiku-20241022"

    # Vector Store & Embeddings Settings
    EMBEDDING_PROVIDER: str = "local"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    CHROMA_DIR: str = "./data/chroma"
    UPLOAD_DIR: str = "./data/uploads"

    # Policy Limits
    MAX_CHAT_MESSAGES: int = 10
    MAX_UPLOAD_MB: int = 10

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def provider_list(self) -> List[str]:
        """Parses comma-separated provider order into a clean list of strings."""
        return [p.strip().lower() for p in self.LLM_PROVIDER_ORDER.split(",") if p.strip()]


# Singleton instance of settings
settings = Settings()
