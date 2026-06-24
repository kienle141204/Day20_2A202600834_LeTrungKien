"""Analyst agent."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient

_SYSTEM_PROMPT = (
    "You are an analyst agent. Extract key claims from the research notes, compare "
    "viewpoints across sources, and flag any weak or unsupported evidence."
)


class AnalystAgent(BaseAgent):
    """Turns research notes into structured insights."""

    name = "analyst"

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.analysis_notes`."""

        sources_text = "\n".join(f"- {s.title} ({s.url})" for s in state.sources)
        user_prompt = (
            f"Research notes:\n{state.research_notes}\n\nSources used:\n{sources_text}"
        )
        response = self._llm.complete(_SYSTEM_PROMPT, user_prompt)
        state.analysis_notes = response.content

        state.agent_results.append(
            AgentResult(
                agent=AgentName.ANALYST,
                content=response.content,
                metadata={
                    "input_tokens": response.input_tokens,
                    "output_tokens": response.output_tokens,
                    "cost_usd": response.cost_usd,
                },
            )
        )
        state.add_trace_event("analyst", {})
        return state
