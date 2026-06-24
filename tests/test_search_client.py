from multi_agent_research_lab.services.search_client import SearchClient


def test_search_client_mock_returns_requested_count() -> None:
    client = SearchClient()
    results = client.search("graphrag", max_results=3)
    assert len(results) == 3
    assert all(r.title and r.snippet for r in results)
