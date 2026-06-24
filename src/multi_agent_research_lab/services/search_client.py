"""Search client abstraction for ResearcherAgent."""

from multi_agent_research_lab.core.config import Settings, get_settings
from multi_agent_research_lab.core.schemas import SourceDocument

# Tavily rejects queries longer than this with "Query is too long".
_TAVILY_MAX_QUERY_LENGTH = 400


class SearchClient:
    """Provider-agnostic search client.

    Uses a deterministic mock backend by default so the lab runs without any API key.
    When `settings.tavily_api_key` is set, a real provider call can be wired in via
    `_search_tavily` without changing the agent-facing interface.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    def search(self, query: str, max_results: int = 5) -> list[SourceDocument]:
        """Search for documents relevant to a query."""

        if self._settings.tavily_api_key:
            return self._search_tavily(query, max_results)
        return self._search_mock(query, max_results)

    def _search_mock(self, query: str, max_results: int) -> list[SourceDocument]:
        """Deterministic offline backend: synthesizes plausible-looking sources."""

        count = min(max_results, 5)
        return [
            SourceDocument(
                title=f"Mock source {i + 1} for '{query}'",
                url=f"https://example.com/mock-source/{i + 1}",
                snippet=(
                    f"Mock excerpt {i + 1}: relevant background information about '{query}'."
                ),
                metadata={"rank": i + 1, "provider": "mock"},
            )
            for i in range(count)
        ]

    def _search_tavily(self, query: str, max_results: int) -> list[SourceDocument]:
        """Real Tavily-backed search.

        Seam for connecting an actual provider once `TAVILY_API_KEY` is configured.
        """

        from tavily import TavilyClient

        client = TavilyClient(api_key=self._settings.tavily_api_key)
        response = client.search(query=query[:_TAVILY_MAX_QUERY_LENGTH], max_results=max_results)
        return [
            SourceDocument(
                title=result.get("title", ""),
                url=result.get("url"),
                snippet=result.get("content", ""),
                metadata={"provider": "tavily"},
            )
            for result in response.get("results", [])
        ]
