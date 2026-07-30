"""LLM factory for creating ChatGoogleGenerativeAI instances."""

from langchain_google_genai import ChatGoogleGenerativeAI

from src.utils.config import Settings


def create_llm(settings: Settings) -> ChatGoogleGenerativeAI:
    """Create a ChatGoogleGenerativeAI instance with the configured model."""
    return ChatGoogleGenerativeAI(
        model=settings.google_model,
        api_key=settings.google_api_key,
        temperature=0.7,
    )
