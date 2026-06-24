"""Shared pytest fixtures."""

import pytest

from multi_agent_research_lab.core.config import Settings


@pytest.fixture
def mock_settings() -> Settings:
    """Settings with all external provider keys disabled, forcing mock backends.

    Unit tests must stay deterministic, free, and offline regardless of what is
    configured in the developer's local `.env` (real OpenAI/Tavily/Langfuse keys).
    """

    settings = Settings()
    settings.openai_api_key = None
    settings.tavily_api_key = None
    settings.langfuse_public_key = None
    settings.langfuse_secret_key = None
    return settings
