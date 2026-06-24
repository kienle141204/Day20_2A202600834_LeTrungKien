from multi_agent_research_lab.core.schemas import ResearchQuery
from multi_agent_research_lab.evaluation.sample_queries import SAMPLE_QUERIES


def test_there_are_exactly_ten_sample_queries() -> None:
    assert len(SAMPLE_QUERIES) == 10


def test_sample_query_ids_are_unique() -> None:
    ids = [q.id for q in SAMPLE_QUERIES]
    assert len(ids) == len(set(ids))


def test_sample_queries_are_valid_research_queries() -> None:
    for sample in SAMPLE_QUERIES:
        request = ResearchQuery(query=sample.query)
        assert request.query == sample.query
        assert sample.domain
