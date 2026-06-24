from multi_agent_research_lab.core.config import Settings
from multi_agent_research_lab.core.schemas import ResearchQuery
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow


def test_workflow_runs_end_to_end(mock_settings: Settings) -> None:
    state = ResearchState(request=ResearchQuery(query="Explain multi-agent systems"))
    result = MultiAgentWorkflow(mock_settings).run(state)

    assert result.research_notes
    assert result.analysis_notes
    assert result.final_answer
    assert "critic" in result.route_history
    assert result.route_history[-1] == "done"
    assert not result.errors
