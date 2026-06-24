from multi_agent_research_lab.services.llm_client import LLMClient


def test_llm_client_mock_returns_deterministic_content() -> None:
    client = LLMClient()
    response = client.complete("system", "what is graphrag?")
    assert response.content
    assert response.input_tokens is not None and response.input_tokens > 0
    assert response.output_tokens is not None and response.output_tokens > 0
    assert response.cost_usd is not None and response.cost_usd >= 0
