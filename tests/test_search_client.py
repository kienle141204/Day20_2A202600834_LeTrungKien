import sys
import types
from typing import Any

import pytest

from multi_agent_research_lab.core.config import Settings
from multi_agent_research_lab.services.search_client import SearchClient


def test_search_client_mock_returns_requested_count(mock_settings: Settings) -> None:
    client = SearchClient(mock_settings)
    results = client.search("graphrag", max_results=3)
    assert len(results) == 3
    assert all(r.title and r.snippet for r in results)
    assert all(r.url and r.url.startswith("https://example.com/mock-source/") for r in results)


def test_search_client_truncates_long_query_for_tavily(
    monkeypatch: pytest.MonkeyPatch, mock_settings: Settings
) -> None:
    captured: dict[str, str] = {}

    class _FakeTavilyClient:
        def __init__(self, api_key: str) -> None:
            pass

        def search(self, query: str, max_results: int) -> dict[str, Any]:
            captured["query"] = query
            return {"results": []}

    fake_module = types.ModuleType("tavily")
    fake_module.TavilyClient = _FakeTavilyClient  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "tavily", fake_module)

    mock_settings.tavily_api_key = "fake-key"
    client = SearchClient(mock_settings)
    client.search("word " * 200, max_results=3)

    assert len(captured["query"]) <= 400
