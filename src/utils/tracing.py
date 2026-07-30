"""LangSmith tracing configuration for SecureOps AI."""

import os
import logging
from typing import Optional

from langsmith import Client

from src.utils.config import get_settings


logger = logging.getLogger(__name__)


def setup_langsmith_tracing() -> Optional[Client]:
    """Initialize LangSmith tracing if enabled.

    Configures LangSmith client for trace collection and monitoring.
    This should be called once at application startup.

    Returns:
        LangSmith Client instance if tracing is enabled, None otherwise.
    """
    settings = get_settings()

    if not settings.langsmith_tracing:
        logger.info("LangSmith tracing is disabled")
        return None

    if not settings.langsmith_api_key:
        logger.warning(
            "LangSmith tracing enabled but LANGSMITH_API_KEY not set. "
            "Set LANGSMITH_TRACING=false or provide LANGSMITH_API_KEY."
        )
        return None

    try:
        # Set environment variables for LangSmith SDK
        os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
        os.environ["LANGSMITH_ENDPOINT"] = settings.langsmith_endpoint
        os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project
        os.environ["LANGSMITH_TRACING"] = "true"

        # Create and test client connection
        client = Client(
            api_key=settings.langsmith_api_key,
            endpoint=settings.langsmith_endpoint,
        )

        # Verify connection by listing projects
        projects = client.list_projects()
        logger.info(
            f"LangSmith tracing enabled for project: {settings.langsmith_project}"
        )

        return client
    except Exception as e:
        logger.error(f"Failed to initialize LangSmith: {str(e)}")
        logger.warning("Continuing without LangSmith tracing")
        return None


def get_langsmith_info() -> dict:
    """Get current LangSmith configuration info.

    Returns:
        Dictionary with tracing status and configuration.
    """
    settings = get_settings()

    return {
        "tracing_enabled": settings.langsmith_tracing,
        "has_api_key": bool(settings.langsmith_api_key),
        "project": settings.langsmith_project,
        "endpoint": settings.langsmith_endpoint,
    }
