"""Command-line entrypoint for the lab starter."""

from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.schemas import ResearchQuery
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.evaluation.benchmark import run_benchmark
from multi_agent_research_lab.evaluation.report import render_markdown_report
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow
from multi_agent_research_lab.observability.logging import configure_logging
from multi_agent_research_lab.observability.tracing import flush_tracing
from multi_agent_research_lab.runners import run_baseline, run_multi_agent
from multi_agent_research_lab.services.storage import LocalArtifactStore

app = typer.Typer(help="Multi-Agent Research Lab starter CLI")
console = Console()


def _init() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)


@app.command()
def baseline(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run a single-agent baseline that completes the task in one LLM call."""

    _init()
    state = run_baseline(query)
    console.print(Panel.fit(state.final_answer or "", title="Single-Agent Baseline"))
    flush_tracing()


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
    flush_tracing()


@app.command()
def benchmark(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run both baseline and multi-agent flows and write a benchmark report."""

    _init()
    _, baseline_metrics = run_benchmark("baseline", query, run_baseline)
    _, multi_metrics = run_benchmark("multi-agent", query, run_multi_agent)

    report = render_markdown_report([baseline_metrics, multi_metrics])
    path = LocalArtifactStore().write_text("benchmark_report.md", report)
    console.print(Panel.fit(report, title="Benchmark Report"))
    console.print(f"[green]Report written to {path}[/green]")
    flush_tracing()


if __name__ == "__main__":
    app()
