"""Command-line entrypoint for the lab starter."""

from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.schemas import AgentName, AgentResult, ResearchQuery
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.evaluation.benchmark import run_benchmark
from multi_agent_research_lab.evaluation.report import render_markdown_report
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow
from multi_agent_research_lab.observability.logging import configure_logging
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.services.storage import LocalArtifactStore

app = typer.Typer(help="Multi-Agent Research Lab starter CLI")
console = Console()

_BASELINE_SYSTEM_PROMPT = (
    "You are a single agent that must research, analyze, and write a final answer to the "
    "user's query in one pass, citing sources where reasonable."
)


def _init() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)


def _run_baseline(query: str) -> ResearchState:
    request = ResearchQuery(query=query)
    state = ResearchState(request=request)
    llm = LLMClient()
    response = llm.complete(_BASELINE_SYSTEM_PROMPT, query)
    state.final_answer = response.content
    state.agent_results.append(
        AgentResult(
            agent=AgentName.SUPERVISOR,
            content=response.content,
            metadata={
                "input_tokens": response.input_tokens,
                "output_tokens": response.output_tokens,
                "cost_usd": response.cost_usd,
            },
        )
    )
    return state


def _run_multi_agent(query: str) -> ResearchState:
    state = ResearchState(request=ResearchQuery(query=query))
    workflow = MultiAgentWorkflow()
    return workflow.run(state)


@app.command()
def baseline(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run a single-agent baseline that completes the task in one LLM call."""

    _init()
    state = _run_baseline(query)
    console.print(Panel.fit(state.final_answer or "", title="Single-Agent Baseline"))


@app.command("multi-agent")
def multi_agent(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run the multi-agent workflow."""

    _init()
    state = ResearchState(request=ResearchQuery(query=query))
    workflow = MultiAgentWorkflow()
    result = workflow.run(state)
    console.print(result.model_dump_json(indent=2))


@app.command()
def benchmark(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run both baseline and multi-agent flows and write a benchmark report."""

    _init()
    _, baseline_metrics = run_benchmark("baseline", query, _run_baseline)
    _, multi_metrics = run_benchmark("multi-agent", query, _run_multi_agent)

    report = render_markdown_report([baseline_metrics, multi_metrics])
    path = LocalArtifactStore().write_text("benchmark_report.md", report)
    console.print(Panel.fit(report, title="Benchmark Report"))
    console.print(f"[green]Report written to {path}[/green]")


if __name__ == "__main__":
    app()
