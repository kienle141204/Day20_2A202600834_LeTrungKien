"""Integration tests against real providers.

These tests exercise the live OpenAI / Tavily / Langfuse seams described in
`services/llm_client.py`, `services/search_client.py`, and `observability/tracing.py`.
They read credentials from the local `.env` (never hardcoded) and are skipped
automatically when the corresponding key is not configured, so they stay safe to
run in any environment (including CI without secrets).
"""

import pytest

from multi_agent_research_lab.core.config import Settings
from multi_agent_research_lab.core.schemas import ResearchQuery
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow
from multi_agent_research_lab.observability.tracing import flush_tracing, trace_span
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.services.search_client import SearchClient

_settings = Settings()

requires_openai = pytest.mark.skipif(
    not _settings.openai_api_key, reason="OPENAI_API_KEY not configured in .env"
)
requires_tavily = pytest.mark.skipif(
    not _settings.tavily_api_key, reason="TAVILY_API_KEY not configured in .env"
)
requires_langfuse = pytest.mark.skipif(
    not (_settings.langfuse_public_key and _settings.langfuse_secret_key),
    reason="Langfuse keys not configured in .env",
)


@requires_openai
def test_openai_real_completion_returns_non_mock_content() -> None:
    client = LLMClient(_settings)
    response = client.complete(
        "You are a concise assistant.", "Reply with exactly the word: pong"
    )
    assert response.content
    assert not response.content.startswith("[mock-llm response]")
    assert response.input_tokens and response.input_tokens > 0
    assert response.output_tokens and response.output_tokens > 0
    assert response.cost_usd is not None and response.cost_usd >= 0


@requires_tavily
def test_tavily_real_search_returns_live_sources() -> None:
    client = SearchClient(_settings)
    results = client.search("GraphRAG state of the art", max_results=3)
    assert results
    assert any(r.url and "example.com" not in r.url for r in results)


@requires_langfuse
def test_langfuse_trace_span_does_not_raise() -> None:
    with trace_span("integration-test-span", {"source": "pytest"}, _settings) as span:
        span["attributes"]["checked"] = True
    flush_tracing()


@requires_openai
@requires_tavily
def test_real_end_to_end_workflow_produces_final_answer() -> None:
    state = ResearchState(request=ResearchQuery(query="What is GraphRAG?"))
    result = MultiAgentWorkflow(_settings).run(state)
    flush_tracing()

    assert result.final_answer
    assert not result.errors
    assert "critic" in result.route_history
    assert result.route_history[-1] == "done"
