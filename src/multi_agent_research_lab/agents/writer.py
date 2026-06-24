"""Writer agent."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient

_SYSTEM_PROMPT = (
    "You are a writer agent. Synthesize the research and analysis notes into a clear, "
    "well-structured final answer for the audience, citing sources where relevant."
)


class WriterAgent(BaseAgent):
    """Produces final answer from research and analysis notes."""

    name = "writer"

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.final_answer`."""

        user_prompt = (
            f"Query: {state.request.query}\n"
            f"Audience: {state.request.audience}\n\n"
            f"Research notes:\n{state.research_notes}\n\n"
            f"Analysis notes:\n{state.analysis_notes}"
        )
        response = self._llm.complete(_SYSTEM_PROMPT, user_prompt)
        state.final_answer = response.content

        state.agent_results.append(
            AgentResult(
                agent=AgentName.WRITER,
                content=response.content,
                metadata={
                    "input_tokens": response.input_tokens,
                    "output_tokens": response.output_tokens,
                    "cost_usd": response.cost_usd,
                },
            )
        )
        state.add_trace_event("writer", {})
        return state
