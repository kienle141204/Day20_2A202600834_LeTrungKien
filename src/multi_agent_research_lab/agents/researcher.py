"""Researcher agent."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.services.search_client import SearchClient

_SYSTEM_PROMPT = (
    "You are a research agent. Summarize the provided sources into concise, "
    "well-cited research notes for the given query."
)


class ResearcherAgent(BaseAgent):
    """Collects sources and creates concise research notes."""

    name = "researcher"

    def __init__(self, llm: LLMClient, search: SearchClient | None = None) -> None:
        self._llm = llm
        self._search = search or SearchClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.sources` and `state.research_notes`."""

        sources = self._search.search(state.request.query, state.request.max_sources)
        state.sources = sources

        sources_text = "\n".join(f"- {s.title}: {s.snippet} ({s.url})" for s in sources)
        user_prompt = f"Query: {state.request.query}\n\nSources:\n{sources_text}"
        response = self._llm.complete(_SYSTEM_PROMPT, user_prompt)
        state.research_notes = response.content

        state.agent_results.append(
            AgentResult(
                agent=AgentName.RESEARCHER,
                content=response.content,
                metadata={
                    "input_tokens": response.input_tokens,
                    "output_tokens": response.output_tokens,
                    "cost_usd": response.cost_usd,
                    "source_count": len(sources),
                },
            )
        )
        state.add_trace_event("researcher", {"source_count": len(sources)})
        return state
