"""Simple Streamlit UI for manually testing the research lab.

Run with:
    streamlit run src/multi_agent_research_lab/ui/streamlit_app.py
"""

from time import perf_counter

import streamlit as st

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.evaluation.benchmark import metrics_from_state
from multi_agent_research_lab.evaluation.report import render_markdown_report
from multi_agent_research_lab.evaluation.sample_queries import SAMPLE_QUERIES
from multi_agent_research_lab.observability.tracing import flush_tracing
from multi_agent_research_lab.runners import run_baseline, run_multi_agent_steps

st.set_page_config(page_title="Multi-Agent Research Lab", layout="wide")
st.title("Multi-Agent Research Lab — Test UI")

settings = get_settings()
backend_label = "real OpenAI/Tavily" if settings.openai_api_key else "mock (offline)"
st.sidebar.caption(f"LLM/search backend: **{backend_label}**")

mode = st.sidebar.radio("Mode", ["Baseline", "Multi-agent", "Benchmark (both)"])

sample_labels = ["(custom query)"] + [f"[{q.domain}] {q.query}" for q in SAMPLE_QUERIES]
choice = st.sidebar.selectbox("Sample mock query", sample_labels)
default_query = (
    "" if choice == sample_labels[0] else SAMPLE_QUERIES[sample_labels.index(choice) - 1].query
)

query = st.text_area("Research query", value=default_query, height=100)
run_clicked = st.button("Run", type="primary", disabled=not query.strip())


def _show_baseline_progress(query: str) -> ResearchState:
    """Run the single-agent baseline as one opaque pass, for contrast with multi-agent."""

    with st.status("Đang chạy Baseline (1 lệnh gọi LLM duy nhất)...", expanded=True) as status:
        status.write("📨 Gửi toàn bộ task (research + analyze + write) trong một prompt...")
        state = run_baseline(query)
        status.write("✅ Đã nhận phản hồi từ LLM.")
        status.update(label="Baseline hoàn tất", state="complete")
    return state


def _show_multi_agent_progress(query: str) -> ResearchState:
    """Run the multi-agent workflow, showing each agent step live as it happens."""

    state: ResearchState | None = None
    with st.status("Đang chạy Multi-agent workflow...", expanded=True) as status:
        for step_state in run_multi_agent_steps(query):
            state = step_state
            if not state.trace:
                continue
            event = state.trace[-1]
            if event["name"] == "route":
                status.write(f"🧭 Supervisor → bước tiếp theo: **{event['payload']['next']}**")
            else:
                status.write(f"✅ Agent **{event['name']}** đã chạy xong — {event['payload']}")
        assert state is not None
        if state.errors:
            status.update(label="Multi-agent dừng vì lỗi", state="error")
        else:
            status.update(label="Multi-agent hoàn tất", state="complete")
    return state


def _show_multi_agent_result(state: ResearchState) -> None:
    st.subheader("Research notes")
    st.write(state.research_notes)
    st.subheader("Analysis notes")
    st.write(state.analysis_notes)
    st.subheader("Final answer")
    st.write(state.final_answer)
    st.subheader("Sources")
    for source in state.sources:
        if source.url:
            st.markdown(f"- [{source.title}]({source.url})")
        else:
            st.markdown(f"- {source.title}")
    if state.errors:
        st.error("\n".join(state.errors))
    with st.expander("Route history / trace"):
        st.json(
            {
                "route_history": state.route_history,
                "critic_passed": state.critic_passed,
                "revision_count": state.revision_count,
                "trace": state.trace,
            }
        )


if run_clicked:
    if mode == "Baseline":
        state = _show_baseline_progress(query)
        st.subheader("Final answer")
        st.write(state.final_answer)

    elif mode == "Multi-agent":
        state = _show_multi_agent_progress(query)
        _show_multi_agent_result(state)

    else:
        st.markdown("### Baseline")
        started = perf_counter()
        baseline_state = _show_baseline_progress(query)
        baseline_metrics = metrics_from_state("baseline", baseline_state, perf_counter() - started)
        st.write(baseline_state.final_answer)

        st.markdown("### Multi-agent")
        started = perf_counter()
        multi_state = _show_multi_agent_progress(query)
        multi_metrics = metrics_from_state("multi-agent", multi_state, perf_counter() - started)
        _show_multi_agent_result(multi_state)

        st.markdown("### Benchmark report")
        st.markdown(render_markdown_report([baseline_metrics, multi_metrics]))

    flush_tracing()
