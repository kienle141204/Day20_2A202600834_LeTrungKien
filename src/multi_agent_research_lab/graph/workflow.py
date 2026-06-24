"""Plain-Python multi-agent workflow (no LangGraph dependency)."""

from collections.abc import Iterator

from multi_agent_research_lab.agents.analyst import AnalystAgent
from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.agents.critic import CriticAgent
from multi_agent_research_lab.agents.researcher import ResearcherAgent
from multi_agent_research_lab.agents.supervisor import DONE, SupervisorAgent
from multi_agent_research_lab.agents.writer import WriterAgent
from multi_agent_research_lab.core.config import Settings, get_settings
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.observability.tracing import trace_span
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.services.search_client import SearchClient


class MultiAgentWorkflow:
    """Builds and runs the multi-agent graph.

    Keep orchestration here; keep agent internals in `agents/`.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._supervisor: SupervisorAgent | None = None
        self._workers: dict[str, BaseAgent] | None = None

    def build(self) -> dict[str, BaseAgent]:
        """Create the supervisor and worker agents, sharing one LLM/search client."""

        llm = LLMClient(self._settings)
        search = SearchClient(self._settings)
        self._supervisor = SupervisorAgent(self._settings)
        self._workers = {
            "researcher": ResearcherAgent(llm, search),
            "analyst": AnalystAgent(llm),
            "writer": WriterAgent(llm),
            "critic": CriticAgent(),
        }
        return self._workers

    def run_steps(self, state: ResearchState) -> Iterator[ResearchState]:
        """Execute the supervisor/worker loop, yielding `state` after every step.

        Lets callers (e.g. a UI) observe progress live instead of only seeing the
        final result. `run()` is implemented on top of this generator.
        """

        if self._workers is None or self._supervisor is None:
            self.build()
        assert self._supervisor is not None
        assert self._workers is not None

        while state.iteration < self._settings.max_iterations:
            with trace_span("supervisor", {"iteration": state.iteration}, self._settings):
                self._supervisor.run(state)
            yield state

            next_route = state.next_route
            if next_route == DONE or next_route is None:
                break

            worker = self._workers.get(next_route)
            if worker is None:
                state.errors.append(f"Unknown route '{next_route}', stopping.")
                yield state
                break

            try:
                with trace_span(next_route, {"iteration": state.iteration}, self._settings):
                    worker.run(state)
            except Exception as exc:  # fallback instead of crashing the workflow
                state.errors.append(f"{next_route} failed: {exc}")
                yield state
                break
            yield state

    def run(self, state: ResearchState) -> ResearchState:
        """Execute the supervisor/worker loop until done or max_iterations is reached."""

        for _ in self.run_steps(state):
            pass
        return state
