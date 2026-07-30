"""Configuration module for SecureOps AI MVP."""

import os
from dataclasses import dataclass


@dataclass
class Settings:
    """Application settings loaded from environment variables."""

    # LLM Configuration
    google_api_key: str
    google_model: str = "gemini-3.5-flash-lite"

    # LangSmith Configuration
    langsmith_tracing: bool = False
    langsmith_api_key: str | None = None
    langsmith_project: str = "SecureOps-SOC-Assistant"
    langsmith_endpoint: str = "https://api.smith.langchain.com"

    # Debug
    debug: bool = False

    @classmethod
    def from_env(cls) -> "Settings":
        """Load settings from environment variables."""
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is required")

        return cls(
            google_api_key=google_api_key,
            google_model=os.getenv("GOOGLE_MODEL", "gemini-3.5-flash-lite"),
            langsmith_tracing=os.getenv("LANGSMITH_TRACING", "false").lower() == "true",
            langsmith_api_key=os.getenv("LANGSMITH_API_KEY"),
            langsmith_project=os.getenv(
                "LANGSMITH_PROJECT", "SecureOps-SOC-Assistant"
            ),
            langsmith_endpoint=os.getenv(
                "LANGSMITH_ENDPOINT", "https://api.smith.langchain.com"
            ),
            debug=os.getenv("DEBUG", "false").lower() == "true",
        )


def get_settings() -> Settings:
    """Get or create the global settings instance."""
    if not hasattr(get_settings, "_instance"):
        get_settings._instance = Settings.from_env()
    return get_settings._instance
