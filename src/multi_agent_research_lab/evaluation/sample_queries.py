"""Sample research queries spanning diverse domains.

One canonical set of mock inputs shared by tests, the benchmark CLI, and the
Streamlit test UI, instead of duplicating query strings in each place.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class SampleQuery:
    id: str
    domain: str
    query: str


SAMPLE_QUERIES: tuple[SampleQuery, ...] = (
    SampleQuery(
        id="ai-rag",
        domain="AI / NLP",
        query=(
            "Research the latest advances in retrieval-augmented generation (RAG) and "
            "summarize the key techniques."
        ),
    ),
    SampleQuery(
        id="health-drug-discovery",
        domain="Healthcare",
        query=(
            "Investigate how AI is being used to accelerate drug discovery and explain "
            "the main approaches."
        ),
    ),
    SampleQuery(
        id="econ-labor",
        domain="Economics",
        query=(
            "Analyze the impact of generative AI on labor markets and summarize the "
            "main findings."
        ),
    ),
    SampleQuery(
        id="climate-carbon-capture",
        domain="Climate",
        query="Research current carbon capture technologies and evaluate their scalability.",
    ),
    SampleQuery(
        id="edu-personalized-learning",
        domain="Education",
        query="Explore how personalized learning platforms use AI to adapt to student needs.",
    ),
    SampleQuery(
        id="cyber-ai-phishing",
        domain="Cybersecurity",
        query=(
            "Research emerging threats from AI-generated phishing attacks and "
            "mitigation strategies."
        ),
    ),
    SampleQuery(
        id="robotics-humanoid",
        domain="Robotics",
        query="Investigate recent breakthroughs in humanoid robotics for industrial automation.",
    ),
    SampleQuery(
        id="finance-llm-trading",
        domain="Finance",
        query=(
            "Research the use of large language models in algorithmic trading and "
            "risk assessment."
        ),
    ),
    SampleQuery(
        id="bio-protein-folding",
        domain="Biology",
        query=(
            "Explore how AlphaFold and similar models are transforming protein "
            "structure prediction."
        ),
    ),
    SampleQuery(
        id="space-reusable-rockets",
        domain="Space",
        query=(
            "Research recent advances in reusable rocket technology and their effect "
            "on launch costs."
        ),
    ),
)
