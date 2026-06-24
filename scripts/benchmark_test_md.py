"""Run baseline vs multi-agent benchmark for each prompt in `test.md`.

Writes a consolidated `benchmark_report.md` (repo root, alongside README.md)
comparing the two agents on every prompt: metrics tables, the full step-by-step
run history (route history, critic verdict, real per-step durations) of each
multi-agent run, and the full final-answer text produced by both agents so the
actual output quality can be read and compared, not just the scores. Run with
real provider keys configured in `.env` for meaningful numbers (mock backends
still run but latency/cost/citation will be trivial).

Usage:
    python scripts/benchmark_test_md.py            # run all prompts
    python scripts/benchmark_test_md.py --prompt 1  # run only Prompt 1
"""

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from typing import Any  # noqa: E402

from multi_agent_research_lab.core.schemas import BenchmarkMetrics  # noqa: E402
from multi_agent_research_lab.core.state import ResearchState  # noqa: E402
from multi_agent_research_lab.evaluation.benchmark import run_benchmark  # noqa: E402
from multi_agent_research_lab.observability import tracing as tracing_module  # noqa: E402
from multi_agent_research_lab.runners import run_baseline, run_multi_agent  # noqa: E402

TEST_MD = ROOT / "test.md"
REPORT_PATH = ROOT / "benchmark_report.md"


def _extract_prompts(text: str) -> list[tuple[str, str]]:
    """Return (title, prompt_text) pairs from the '## Prompt N: ...' sections."""

    sections = re.split(r"^## (Prompt \d+: .+)$", text, flags=re.MULTILINE)
    pairs: list[tuple[str, str]] = []
    for i in range(1, len(sections), 2):
        title = sections[i].strip()
        body = sections[i + 1]
        match = re.search(r"```text\n(.*?)\n```", body, flags=re.DOTALL)
        if match:
            pairs.append((title, match.group(1).strip()))
    return pairs


def _row(prompt_title: str, metrics: BenchmarkMetrics) -> str:
    cost = "" if metrics.estimated_cost_usd is None else f"{metrics.estimated_cost_usd:.4f}"
    quality = "" if metrics.quality_score is None else f"{metrics.quality_score:.1f}"
    return (
        f"| {prompt_title} | {metrics.run_name} | {metrics.latency_seconds:.2f} | "
        f"{cost} | {quality} | {metrics.notes} |"
    )


def _baseline_history(state: ResearchState) -> list[str]:
    lines = ["- 1 lần gọi LLM duy nhất (research + analyze + write trong một prompt)."]
    if state.agent_results:
        meta = state.agent_results[0].metadata
        lines.append(
            f"  - input_tokens={meta.get('input_tokens')}, "
            f"output_tokens={meta.get('output_tokens')}, cost_usd={meta.get('cost_usd')}"
        )
    if state.errors:
        lines.append(f"  - LỖI: {state.errors}")
    return lines


def _multi_agent_history(state: ResearchState, spans: list[dict[str, Any]]) -> list[str]:
    lines = [f"- route_history: `{state.route_history}`"]
    lines.append(
        f"- critic_passed: `{state.critic_passed}` | revision_count: `{state.revision_count}`"
    )
    if state.critic_findings:
        lines.append(f"- critic_findings: {state.critic_findings}")
    lines.append("- Trace từng bước (tên — thời gian thật — payload):")
    for i, (event, span) in enumerate(zip(state.trace, spans, strict=False), start=1):
        duration = span.get("duration_seconds")
        duration_str = f"{duration:.3f}s" if isinstance(duration, (int, float)) else "?"
        lines.append(f"  {i}. `{event['name']}` ({duration_str}) — payload={event['payload']}")
    if state.errors:
        lines.append(f"- LỖI: {state.errors}")
    return lines


def _answer_block(label: str, answer: str | None) -> list[str]:
    lines = [f"<details><summary>{label} — xem câu trả lời đầy đủ</summary>", ""]
    lines.append(answer.strip() if answer else "_(không có câu trả lời — xem mục LỖI ở trên)_")
    lines += ["", "</details>"]
    return lines


def _quality_formula_explanation() -> list[str]:
    return [
        "Quality score (thang 0–10) được tính trong "
        "`evaluation/benchmark.py::_quality_score` theo công thức:",
        "",
        "```",
        "quality_score = max(0, min(10, length_score + citation_score + base - error_penalty))",
        "```",
        "",
        "Trong đó:",
        "",
        "- **`length_score` (tối đa 6 điểm)** — đo độ đầy đủ của câu trả lời theo số từ:",
        "  `length_score = min(số_từ(final_answer) / 150, 1.0) * 6`.",
        "  Câu trả lời ≥150 từ được full 6 điểm; ngắn hơn thì tính theo tỉ lệ "
        "(ví dụ 75 từ → 3 điểm).",
        "- **`citation_score` (tối đa 3 điểm)** — đo mức độ trích dẫn nguồn đúng cách:",
        "  `citation_score = citation_coverage * 3`, với",
        "  `citation_coverage = |trích dẫn hợp lệ| / |tổng số nguồn|`.",
        "  Trích dẫn hợp lệ là các số `[n]` xuất hiện trong `final_answer` (lấy bằng regex "
        "`\\[(\\d+)\\]`) mà `1 <= n <= len(state.sources)`. Nếu agent không có `sources` "
        "(baseline không tìm kiếm web) hoặc chưa có `final_answer` → `citation_coverage = "
        "None` → `citation_score = 0`.",
        "- **`base` = 1 điểm cố định**, chỉ cộng nếu đã có `final_answer` (không thì toàn bộ "
        "`quality_score = 0`).",
        "- **`error_penalty` = 1 điểm bị trừ** nếu `state.errors` không rỗng (agent gặp lỗi "
        "thực thi ở bất kỳ bước nào), ngược lại = 0.",
        "- Kết quả cuối được kẹp (`clamp`) trong khoảng `[0, 10]`.",
        "",
        "Nói cách khác: **6 điểm cho độ dài/đầy đủ câu trả lời + 3 điểm cho việc trích dẫn "
        "nguồn chính xác + 1 điểm nền − 1 điểm nếu có lỗi.** Đây là một heuristic đơn giản "
        "(không dùng LLM-as-judge), ưu tiên đo được, lặp lại được, và không tốn thêm chi phí "
        "gọi model — nhưng vì vậy nó không đánh giá được tính *đúng đắn* hay *độ sâu lập luận* "
        "thực sự của nội dung, chỉ đo độ dài và việc có trích dẫn nguồn hợp lệ hay không.",
        "",
        "Lý do baseline (không có bước Researcher/`sources`) luôn có `citation_coverage = "
        "None` → mất hẳn 3 điểm citation, trong khi multi-agent có `sources` thật từ Tavily "
        "và được Writer yêu cầu trích dẫn `[n]` khớp danh sách nguồn, được Critic kiểm tra lại "
        "— đây chính là phần chênh lệch quality lớn nhất giữa hai agent trong bảng trên.",
    ]


def _sources_block(state: ResearchState) -> list[str]:
    if not state.sources:
        return []
    lines = ["**Nguồn (multi-agent đã tìm và trích dẫn):**", ""]
    for i, source in enumerate(state.sources, start=1):
        lines.append(f"{i}. [{source.title}]({source.url}) — {source.snippet}")
    return lines


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--prompt",
        type=int,
        default=None,
        help="1-indexed prompt number to run (default: run all prompts).",
    )
    args = parser.parse_args()

    prompts = _extract_prompts(TEST_MD.read_text(encoding="utf-8"))
    if not prompts:
        raise SystemExit(f"No '## Prompt N: ...' sections with a ```text block found in {TEST_MD}")
    if args.prompt is not None:
        if not 1 <= args.prompt <= len(prompts):
            raise SystemExit(f"--prompt must be between 1 and {len(prompts)}")
        prompts = [prompts[args.prompt - 1]]

    Result = tuple[
        str, ResearchState, BenchmarkMetrics, ResearchState, BenchmarkMetrics, list[dict[str, Any]]
    ]
    results: list[Result] = []
    for title, prompt in prompts:
        print(f"--- Running: {title} ---", flush=True)
        print("  baseline...", flush=True)
        baseline_state, baseline_metrics = run_benchmark("baseline", prompt, run_baseline)
        print(f"    latency={baseline_metrics.latency_seconds:.2f}s", flush=True)
        print("  multi-agent...", flush=True)
        span_start = len(tracing_module.spans)
        multi_state, multi_metrics = run_benchmark("multi-agent", prompt, run_multi_agent)
        multi_spans = tracing_module.spans[span_start:]
        print(f"    latency={multi_metrics.latency_seconds:.2f}s", flush=True)
        results.append(
            (title, baseline_state, baseline_metrics, multi_state, multi_metrics, multi_spans)
        )

    lines = [
        "# Benchmark Report — Baseline vs Multi-agent (prompts from test.md)",
        "",
        "## Bảng tổng hợp",
        "",
        "| Prompt | Run | Latency (s) | Cost (USD) | Quality | Notes |",
        "|---|---|---:|---:|---:|---|",
    ]
    for title, _, baseline_metrics, _, multi_metrics, _ in results:
        lines.append(_row(title, baseline_metrics))
        lines.append(_row(title, multi_metrics))

    lines += ["", "## Cách tính Quality Score", ""]
    lines.extend(_quality_formula_explanation())

    lines += [
        "",
        "## Delta theo từng prompt (multi-agent − baseline)",
        "",
        "| Prompt | Δ Latency (s) | Δ Cost (USD) | Δ Quality |",
        "|---|---:|---:|---:|",
    ]
    for title, _, baseline_metrics, _, multi_metrics, _ in results:
        d_lat = multi_metrics.latency_seconds - baseline_metrics.latency_seconds
        d_cost = (multi_metrics.estimated_cost_usd or 0.0) - (
            baseline_metrics.estimated_cost_usd or 0.0
        )
        d_quality = (multi_metrics.quality_score or 0.0) - (baseline_metrics.quality_score or 0.0)
        lines.append(f"| {title} | {d_lat:+.2f} | {d_cost:+.4f} | {d_quality:+.1f} |")

    lines += ["", "## Lịch sử quá trình chạy chi tiết theo từng prompt", ""]
    for title, baseline_state, baseline_metrics, multi_state, multi_metrics, multi_spans in results:
        lines.append(f"### {title}")
        lines.append("")
        lines.append(f"**Query:** {baseline_state.request.query}")
        lines.append("")
        lines.append(f"**Baseline** (latency={baseline_metrics.latency_seconds:.2f}s):")
        lines.extend(_baseline_history(baseline_state))
        lines.append("")
        lines.extend(_answer_block("Baseline", baseline_state.final_answer))
        lines.append("")
        lines.append(f"**Multi-agent** (latency={multi_metrics.latency_seconds:.2f}s):")
        lines.extend(_multi_agent_history(multi_state, multi_spans))
        lines.append("")
        lines.extend(_answer_block("Multi-agent", multi_state.final_answer))
        lines.append("")
        lines.extend(_sources_block(multi_state))
        lines.append("")

    report = "\n".join(lines) + "\n"
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"\nReport written to {REPORT_PATH}")


if __name__ == "__main__":
    main()
