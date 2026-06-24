"""Benchmark report rendering."""

from multi_agent_research_lab.core.schemas import BenchmarkMetrics


def _format_delta(label: str, base: float | None, other: float | None, unit: str = "") -> str:
    if base is None or other is None:
        return f"- {label}: n/a"
    delta = other - base
    sign = "+" if delta >= 0 else ""
    return (
        f"- {label}: {sign}{delta:.3f}{unit} "
        f"(baseline={base:.3f}{unit}, other={other:.3f}{unit})"
    )


def render_markdown_report(metrics: list[BenchmarkMetrics]) -> str:
    """Render benchmark metrics to markdown, including a single-vs-multi comparison."""

    lines = [
        "# Benchmark Report",
        "",
        "| Run | Latency (s) | Cost (USD) | Quality | Notes |",
        "|---|---:|---:|---:|---|",
    ]
    for item in metrics:
        cost = "" if item.estimated_cost_usd is None else f"{item.estimated_cost_usd:.4f}"
        quality = "" if item.quality_score is None else f"{item.quality_score:.1f}"
        lines.append(
            f"| {item.run_name} | {item.latency_seconds:.2f} | {cost} | {quality} | "
            f"{item.notes} |"
        )

    baseline = next((m for m in metrics if m.run_name == "baseline"), None)
    multi = next((m for m in metrics if m.run_name == "multi-agent"), None)
    if baseline and multi:
        lines += [
            "",
            "## Single-agent vs Multi-agent",
            "",
            _format_delta("Latency", baseline.latency_seconds, multi.latency_seconds, "s"),
            _format_delta("Cost", baseline.estimated_cost_usd, multi.estimated_cost_usd, " USD"),
            _format_delta("Quality", baseline.quality_score, multi.quality_score),
        ]

    return "\n".join(lines) + "\n"
