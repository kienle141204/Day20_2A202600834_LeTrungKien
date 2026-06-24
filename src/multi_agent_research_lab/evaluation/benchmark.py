"""Benchmark utilities for single-agent vs multi-agent comparison."""

from collections.abc import Callable
from time import perf_counter

from multi_agent_research_lab.core.schemas import BenchmarkMetrics, ResearchQuery
from multi_agent_research_lab.core.state import ResearchState

Runner = Callable[[str], ResearchState]


def _estimate_cost(state: ResearchState) -> float:
    return sum(
        result.metadata.get("cost_usd") or 0.0
        for result in state.agent_results
        if isinstance(result.metadata.get("cost_usd"), (int, float))
    )


def _citation_coverage(state: ResearchState) -> float | None:
    if not state.sources or not state.final_answer:
        return None
    cited = sum(1 for s in state.sources if s.url and s.url in state.final_answer)
    return cited / len(state.sources)


def _quality_score(state: ResearchState, citation_coverage: float | None) -> float:
    if not state.final_answer:
        return 0.0
    length_score = min(len(state.final_answer.split()) / 150, 1.0) * 6
    citation_score = (citation_coverage or 0.0) * 3
    error_penalty = 1.0 if state.errors else 0.0
    return max(0.0, min(10.0, length_score + citation_score + 1.0 - error_penalty))


def run_benchmark(
    run_name: str, query: str, runner: Runner
) -> tuple[ResearchState, BenchmarkMetrics]:
    """Run `runner`, measure latency, and compute cost/quality/citation/error metrics."""

    started = perf_counter()
    try:
        state = runner(query)
        failed = False
    except Exception as exc:
        state = ResearchState(request=ResearchQuery(query=query))
        state.errors.append(str(exc))
        failed = True
    latency = perf_counter() - started

    citation_coverage = _citation_coverage(state)
    quality_score = _quality_score(state, citation_coverage)
    notes_parts = [
        f"errors={len(state.errors)}",
        f"error_rate={1.0 if failed else (1.0 if state.errors else 0.0):.2f}",
    ]
    if citation_coverage is not None:
        notes_parts.append(f"citation_coverage={citation_coverage:.2f}")

    metrics = BenchmarkMetrics(
        run_name=run_name,
        latency_seconds=latency,
        estimated_cost_usd=_estimate_cost(state) or None,
        quality_score=quality_score,
        notes=", ".join(notes_parts),
    )
    return state, metrics
