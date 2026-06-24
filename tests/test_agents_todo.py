from multi_agent_research_lab.agents import (
    AnalystAgent,
    CriticAgent,
    ResearcherAgent,
    SupervisorAgent,
    WriterAgent,
)
from multi_agent_research_lab.core.config import Settings
from multi_agent_research_lab.core.schemas import ResearchQuery, SourceDocument
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


def test_supervisor_routes_through_analyst_writer_critic() -> None:
    state = _state()
    state.research_notes = "notes"
    SupervisorAgent().run(state)
    assert state.next_route == "analyst"

    state.analysis_notes = "analysis"
    SupervisorAgent().run(state)
    assert state.next_route == "writer"

    state.final_answer = "answer"
    SupervisorAgent().run(state)
    assert state.next_route == "critic"


def test_supervisor_revises_once_then_stops() -> None:
    settings = Settings()
    state = _state()
    state.research_notes = "notes"
    state.analysis_notes = "analysis"
    state.final_answer = "a weak draft"
    state.critic_passed = False

    SupervisorAgent(settings).run(state)
    assert state.next_route == "writer"
    assert state.revision_count == 1

    state.critic_passed = False
    SupervisorAgent(settings).run(state)
    assert state.next_route == "done"
    assert state.revision_count == 1


def test_supervisor_done_when_critic_passes() -> None:
    state = _state()
    state.research_notes = "notes"
    state.analysis_notes = "analysis"
    state.final_answer = "answer"
    state.critic_passed = True
    SupervisorAgent().run(state)
    assert state.next_route == "done"


def test_supervisor_stops_at_max_iterations() -> None:
    settings = Settings()
    settings.max_iterations = 1
    state = _state()
    state.iteration = 1
    SupervisorAgent(settings).run(state)
    assert state.next_route == "done"


def test_researcher_populates_sources_and_notes(mock_settings: Settings) -> None:
    state = _state()
    ResearcherAgent(LLMClient(mock_settings), SearchClient(mock_settings)).run(state)
    assert state.sources
    assert state.research_notes


def test_analyst_populates_analysis_notes(mock_settings: Settings) -> None:
    state = _state()
    state.research_notes = "some research notes"
    AnalystAgent(LLMClient(mock_settings)).run(state)
    assert state.analysis_notes


def test_writer_populates_final_answer_and_resets_critic_state(mock_settings: Settings) -> None:
    state = _state()
    state.research_notes = "some research notes"
    state.analysis_notes = "some analysis notes"
    state.sources = [SourceDocument(title="A source", url="https://example.com/a", snippet="x")]
    WriterAgent(LLMClient(mock_settings)).run(state)
    assert state.final_answer
    assert state.critic_passed is None
    assert state.critic_findings == []


def test_critic_flags_missing_final_answer() -> None:
    state = _state()
    CriticAgent().run(state)
    assert state.critic_passed is False
    assert "No final answer produced." in state.critic_findings


def test_critic_flags_missing_citation() -> None:
    state = _state()
    state.sources = [SourceDocument(title="A source", url="https://example.com/a", snippet="x")]
    state.final_answer = " ".join(["word"] * 30)
    CriticAgent().run(state)
    assert state.critic_passed is False
    assert any("cite" in f for f in state.critic_findings)


def test_critic_passes_with_valid_citation() -> None:
    state = _state()
    state.sources = [SourceDocument(title="A source", url="https://example.com/a", snippet="x")]
    state.final_answer = " ".join(["word"] * 30) + " [1]"
    CriticAgent().run(state)
    assert state.critic_passed is True
    assert state.critic_findings == []
