from multi_agent_research_lab.core.schemas import ResearchQuery
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.evaluation.benchmark import run_benchmark


def _fake_runner(query: str) -> ResearchState:
    state = ResearchState(request=ResearchQuery(query=query))
    state.final_answer = "a reasonably long final answer with enough words to score well here"
    return state


def test_run_benchmark_computes_latency_and_quality() -> None:
    state, metrics = run_benchmark("baseline", "Explain multi-agent systems", _fake_runner)
    assert state.final_answer
    assert metrics.run_name == "baseline"
    assert metrics.latency_seconds >= 0
    assert metrics.quality_score is not None
    assert "error_rate" in metrics.notes
