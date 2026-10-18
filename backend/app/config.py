"""Configuration management module for the Network Complaint Portal backend.

This module reads application settings from environment variables using
Pydantic Settings, providing type verification and default values for local development.

Key Configurations:
- Database connection (MongoDB URI and database name)
- Admin authentication parameters (username, bcrypt password hash, JWT secret)
- Multi-provider LLM & Vector Store settings (Gemini, OpenAI, Grok, Anthropic, Mock)
- Application rules (Max chat messages limit, upload file size cap)
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

    # MongoDB Settings
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "network_portal"

    # Authentication & JWT Security
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD_HASH: str = "$2b$12$z11TCwrLVRnlzFvMTKV2suLuuSeDTrATQJN2.b0ZARDdcuzbnyyhm"
    JWT_SECRET: str = "mnnit-network-portal-jwt-secret-key-32bytes-min"
    JWT_EXPIRE_HOURS: int = 8

    # Multi-Provider LLM Fallback Configuration
    # Order of providers to try (e.g., 'gemini,openai,grok,anthropic,mock')
    LLM_PROVIDER_ORDER: str = "gemini,openai,grok,anthropic,mock"

    # Provider API Keys
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    GROK_API_KEY: str = ""
    LLM_API_KEY: str = ""  # Anthropic API Key

    # Provider Models
    GEMINI_MODEL: str = "gemini-1.5-flash"
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
    ALLOWED_EMAIL_DOMAIN: str | None = None

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
