"""Shared single-call entrypoints for baseline / multi-agent execution.

Used by both the CLI and the Streamlit test UI so there is one place that defines
what "running baseline" and "running multi-agent" mean.
"""

from collections.abc import Iterator

from multi_agent_research_lab.core.schemas import AgentName, AgentResult, ResearchQuery
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow
from multi_agent_research_lab.services.llm_client import LLMClient

_BASELINE_SYSTEM_PROMPT = (
    "You are a single agent that must research, analyze, and write a final answer to the "
    "user's query in one pass, citing sources where reasonable."
)


def run_baseline(query: str) -> ResearchState:
    """Single LLM call doing research + analysis + writing in one pass."""

    state = ResearchState(request=ResearchQuery(query=query))
    response = LLMClient().complete(_BASELINE_SYSTEM_PROMPT, query)
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


def run_multi_agent(query: str) -> ResearchState:
    """Full Supervisor/Researcher/Analyst/Writer/Critic workflow."""

    state = ResearchState(request=ResearchQuery(query=query))
    return MultiAgentWorkflow().run(state)


def run_multi_agent_steps(query: str) -> Iterator[ResearchState]:
    """Same as `run_multi_agent`, but yields `state` after every workflow step.

    Used by the Streamlit UI to show live progress instead of only the final result.
    """

    state = ResearchState(request=ResearchQuery(query=query))
    yield from MultiAgentWorkflow().run_steps(state)
