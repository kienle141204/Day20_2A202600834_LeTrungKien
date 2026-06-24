from multi_agent_research_lab.agents import (
    AnalystAgent,
    ResearcherAgent,
    SupervisorAgent,
    WriterAgent,
)
from multi_agent_research_lab.core.config import Settings
from multi_agent_research_lab.core.schemas import ResearchQuery
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.services.search_client import SearchClient


def _state() -> ResearchState:
    return ResearchState(request=ResearchQuery(query="Explain multi-agent systems"))


def test_supervisor_routes_to_researcher_when_no_notes() -> None:
    state = _state()
    SupervisorAgent().run(state)
    assert state.next_route == "researcher"
    assert state.route_history == ["researcher"]


def test_supervisor_routes_through_analyst_writer_then_done() -> None:
    state = _state()
    state.research_notes = "notes"
    SupervisorAgent().run(state)
    assert state.next_route == "analyst"

    state.analysis_notes = "analysis"
    SupervisorAgent().run(state)
    assert state.next_route == "writer"

    state.final_answer = "answer"
    SupervisorAgent().run(state)
    assert state.next_route == "done"


def test_supervisor_stops_at_max_iterations() -> None:
    settings = Settings()
    settings.max_iterations = 1
    state = _state()
    state.iteration = 1
    SupervisorAgent(settings).run(state)
    assert state.next_route == "done"


def test_researcher_populates_sources_and_notes() -> None:
    state = _state()
    ResearcherAgent(LLMClient(), SearchClient()).run(state)
    assert state.sources
    assert state.research_notes


def test_analyst_populates_analysis_notes() -> None:
    state = _state()
    state.research_notes = "some research notes"
    AnalystAgent(LLMClient()).run(state)
    assert state.analysis_notes


def test_writer_populates_final_answer() -> None:
    state = _state()
    state.research_notes = "some research notes"
    state.analysis_notes = "some analysis notes"
    WriterAgent(LLMClient()).run(state)
    assert state.final_answer
