# Benchmark Report — Baseline vs Multi-agent (prompts from test.md)

## Bảng tổng hợp

| Prompt | Run | Latency (s) | Cost (USD) | Quality | Notes |
|---|---|---:|---:|---:|---|
| Prompt 1: ResearchAgentBench Benchmark Design | baseline | 14.19 | 0.0007 | 7.0 | errors=0, error_rate=0.00 |
| Prompt 1: ResearchAgentBench Benchmark Design | multi-agent | 43.19 | 0.0025 | 10.0 | errors=0, error_rate=0.00, citation_coverage=1.00 |

## Cách tính Quality Score

Quality score (thang 0–10) được tính trong `evaluation/benchmark.py::_quality_score` theo công thức:

```
quality_score = max(0, min(10, length_score + citation_score + base - error_penalty))
```

Trong đó:

- **`length_score` (tối đa 6 điểm)** — đo độ đầy đủ của câu trả lời theo số từ:
  `length_score = min(số_từ(final_answer) / 150, 1.0) * 6`.
  Câu trả lời ≥150 từ được full 6 điểm; ngắn hơn thì tính theo tỉ lệ (ví dụ 75 từ → 3 điểm).
- **`citation_score` (tối đa 3 điểm)** — đo mức độ trích dẫn nguồn đúng cách:
  `citation_score = citation_coverage * 3`, với
  `citation_coverage = |trích dẫn hợp lệ| / |tổng số nguồn|`.
  Trích dẫn hợp lệ là các số `[n]` xuất hiện trong `final_answer` (lấy bằng regex `\[(\d+)\]`) mà `1 <= n <= len(state.sources)`. Nếu agent không có `sources` (baseline không tìm kiếm web) hoặc chưa có `final_answer` → `citation_coverage = None` → `citation_score = 0`.
- **`base` = 1 điểm cố định**, chỉ cộng nếu đã có `final_answer` (không thì toàn bộ `quality_score = 0`).
- **`error_penalty` = 1 điểm bị trừ** nếu `state.errors` không rỗng (agent gặp lỗi thực thi ở bất kỳ bước nào), ngược lại = 0.
- Kết quả cuối được kẹp (`clamp`) trong khoảng `[0, 10]`.

Nói cách khác: **6 điểm cho độ dài/đầy đủ câu trả lời + 3 điểm cho việc trích dẫn nguồn chính xác + 1 điểm nền − 1 điểm nếu có lỗi.** Đây là một heuristic đơn giản (không dùng LLM-as-judge), ưu tiên đo được, lặp lại được, và không tốn thêm chi phí gọi model — nhưng vì vậy nó không đánh giá được tính *đúng đắn* hay *độ sâu lập luận* thực sự của nội dung, chỉ đo độ dài và việc có trích dẫn nguồn hợp lệ hay không.

Lý do baseline (không có bước Researcher/`sources`) luôn có `citation_coverage = None` → mất hẳn 3 điểm citation, trong khi multi-agent có `sources` thật từ Tavily và được Writer yêu cầu trích dẫn `[n]` khớp danh sách nguồn, được Critic kiểm tra lại — đây chính là phần chênh lệch quality lớn nhất giữa hai agent trong bảng trên.

## Delta theo từng prompt (multi-agent − baseline)

| Prompt | Δ Latency (s) | Δ Cost (USD) | Δ Quality |
|---|---:|---:|---:|
| Prompt 1: ResearchAgentBench Benchmark Design | +29.00 | +0.0018 | +3.0 |

## Lịch sử quá trình chạy chi tiết theo từng prompt

### Prompt 1: ResearchAgentBench Benchmark Design

**Query:** You are part of a university lab designing a benchmark to evaluate AI systems that assist students with research tasks.

Your task is to design a benchmark called ResearchAgentBench.

The benchmark should evaluate whether an AI system can actually help a graduate student complete research work, not just produce fluent text.

You must produce a full benchmark design document that includes:
1. Benchmark goal
2. Core assumptions
3. Task categories
4. At least 12 example tasks across different categories
5. A scoring rubric
6. Baselines to compare against
7. Likely failure modes and gaming risks
8. Human evaluation protocol
9. Limitations of the benchmark
10. Recommendations for version 2 of the benchmark

Constraints:
- The benchmark must be realistic for a small academic lab
- It must not depend on expensive annotation
- It must distinguish between usefulness, correctness, and research judgment
- It must include at least one adversarial or stress-test component
- It must explicitly discuss how systems might game the evaluation

Output format:
Write this as a mini design document suitable for discussion in a research lab meeting.

**Baseline** (latency=14.19s):
- 1 lần gọi LLM duy nhất (research + analyze + write trong một prompt).
  - input_tokens=265, output_tokens=1093, cost_usd=0.00069555

<details><summary>Baseline — xem câu trả lời đầy đủ</summary>

## ResearchAgentBench Design Document

### 1. Benchmark Goal
The primary goal of ResearchAgentBench is to evaluate the effectiveness of AI systems in assisting graduate students with research tasks. It aims to measure not only the fluency of generated text but also the practical usefulness, correctness, and the quality of research judgment exhibited by the AI in real-world academic scenarios.

### 2. Core Assumptions
- AI systems are intended to enhance the research process, not replace human researchers.
- Effective research assistance involves finding relevant literature, synthesizing information, and providing actionable insights based on that information.
- The benchmark will account for variability in research disciplines and individual user needs.

### 3. Task Categories
1. **Literature Review**: Tasks that require the AI to identify, summarize, and analyze relevant academic papers.
2. **Data Analysis**: Tasks involving interpretation of data or results from studies.
3. **Research Proposal**: Tasks requiring the generation of research questions and proposed methodologies.
4. **Synthesis and Application**: Tasks that ask the AI to combine findings across multiple sources to make specific recommendations.
5. **Adversarial Stress Tests**: Designed to evaluate how AI responds to misleading queries or ambiguous prompts.

### 4. Example Tasks across Different Categories
1. **Literature Review Task**: "Identify five key papers published in the last five years on the topic of neural networks in healthcare and provide a summary of their findings."
2. **Data Analysis Task**: "Given the attached dataset, analyze the correlations between variable X and Y and provide possible explanations for your observations."
3. **Research Proposal Task**: "Formulate a research proposal outline on the impact of climate change on migratory bird patterns, including initial hypotheses and planned methodologies."
4. **Synthesis Task**: "Summarize the implications of conflicting studies on the efficacy of remote learning on student engagement found within ten different articles."
5. **Stress Test Task**: "Provide a literature review on the effects of unicorns on academic integrity, which is an obviously fictional prompt."
6. **Data Analysis Task**: "Critically evaluate the statistical methods used in this research paper and suggest improvements."
7. **Literature Review Task**: "Retrieve and summarize the top three most cited papers on quantum computing from the last decade."
8. **Synthesis Task**: "Propose a hypothesis based on findings from two contrasting studies on renewable energy investments."
9. **Research Proposal Task**: "Draft a hypothesis for researching the socioeconomic impacts of a possible recession on high school dropout rates."
10. **Stress Test Task**: "Develop a summary of the literature that covers multi-disciplinary research on parapsychology."
11. **Synthesis Task**: "Compare and contrast two theoretical frameworks in the context of their applicability to online marketing."
12. **Research Proposal Task**: "Outline the potential ethical considerations in AI applications in healthcare."

### 5. Scoring Rubric
- **Usefulness (40%)**: Does the output provide relevant support for completing the task?
- **Correctness (30%)**: Are the facts and citations accurate?
- **Research Judgment (30%)**: Is the synthesis of information logical, and does it demonstrate a deeper understanding of the topic?
  
Scores can range from 0 (not useful/correct) to 5 (extremely useful/correct), with average scores calculated for overall performance.

### 6. Baselines to Compare Against
- **Human Baseline**: Use an average score from a cohort of graduate students completing the same tasks.
- **Previous AI Systems**: Compare against well-known AI systems like OpenAI's GPT series or Google’s Bard on selected tasks to validate incremental improvements.

### 7. Likely Failure Modes and Gaming Risks
- **Misleading Outputs**: AI may generate plausible-sounding but incorrect information, particularly in stress test scenarios.
- **Overfitting to Benchmark**: AI systems could be designed to exploit specific phrasing or structures in the tasks.
- **Superficial Responses**: Systems may produce fluent text without real depth or understanding, failing to add value to the research process.

### 8. Human Evaluation Protocol
- Selection of graduate students as evaluators to assess outputs on a 1-5 scale according to the scoring rubric.
- Use of double-blind assessments to minimize bias; evaluators should not know which AI system produced the output.
- Regular calibration meetings to ensure evaluators are aligned on the rubric criteria.

### 9. Limitations of the Benchmark
- May not fully capture the nuanced needs of different academic disciplines.
- The benchmarking tasks are limited to predefined scenarios which might not encompass all real-world situations a graduate student may face.
- Human evaluators may have subjective biases affecting the quality of assessments.

### 10. Recommendations for Version 2 of the Benchmark
- Expand task categories to include more interdisciplinary and interdisciplinary prompts.
- Introduce longer-term tasks that simulate ongoing research processes rather than discrete tasks.
- Implement more dynamic scoring mechanisms that adjust for task ambiguity and context, rather than a static rubric.
- Explore incorporating peer review scenarios where AI must evaluate or critique other AI-generated work as a new layer of complexity and realism.

This document serves as a foundational framework for developing and deploying ResearchAgentBench as an effective assessment tool for AI systems assisting graduate students in research.

</details>

**Multi-agent** (latency=43.19s):
- route_history: `['researcher', 'analyst', 'writer', 'critic', 'done']`
- critic_passed: `True` | revision_count: `0`
- Trace từng bước (tên — thời gian thật — payload):
  1. `route` (0.798s) — payload={'next': 'researcher'}
  2. `researcher` (14.551s) — payload={'source_count': 5}
  3. `route` (0.001s) — payload={'next': 'analyst'}
  4. `analyst` (9.878s) — payload={}
  5. `route` (0.001s) — payload={'next': 'writer'}
  6. `writer` (17.949s) — payload={}
  7. `route` (0.001s) — payload={'next': 'critic'}
  8. `critic` (0.001s) — payload={'issue_count': 0}
  9. `route` (0.000s) — payload={'next': 'done'}

<details><summary>Multi-agent — xem câu trả lời đầy đủ</summary>

# ResearchAgentBench Design Document

## 1. Benchmark Goal
The primary goal of **ResearchAgentBench** is to evaluate the effectiveness of AI systems in assisting graduate students with diverse research tasks. Unlike prior assessments that focus solely on fluent text generation, this benchmark aims to measure utility, accuracy, and informed judgment within the context of academic research, thereby providing a deeper insight into how AI can meaningfully contribute to research processes.

## 2. Core Assumptions
- AI systems can offer substantial help beyond simple text generation, thereby streamlining the research workflow for graduate students.
- Effective evaluation must encompass key components of research, including information retrieval, synthesis, critical thinking, and ethics.
- The benchmark is designed to be practical and affordable for small academic labs, relying on accessible resources without requiring extensive annotation or infrastructure investments.

## 3. Task Categories
1. **Literature Review**
2. **Research Design & Methodology**
3. **Data Analysis**
4. **Report Writing & Presentation**
5. **Ethical Considerations in Research**
6. **Adversarial Tasks & Stress Testing**

## 4. Example Tasks
1. **Literature Review**: Identify and summarize five seminal papers on a topic, pinpointing key contributions and methodologies.
2. **Research Design**: Formulate a research question and outline a comprehensive study design involving sample selection and data collection strategies.
3. **Data Analysis**: Analyze and interpret a provided dataset, creating descriptive statistics and discussing the implications of the results.
4. **Report Writing**: Draft a 500-word research report that encapsulates findings from a specific investigation, adhering to academic standards.
5. **Ethical Considerations**: Evaluate a given research proposal for ethical implications and suggest strategies to address potential issues.
6. **Adversarial Task**: Assess a deliberately misleading dataset and outline the pitfalls potentially influencing result interpretation.
7. **Synthesis Task**: Integrate insights from three different scholarly sources to generate a novel research hypothesis.
8. **Framework Application**: Utilize a specified research framework (e.g., qualitative vs. quantitative) to analyze a given topic, justifying your choice with rationale.
9. **Presentation Preparation**: Create a presentation (PowerPoint) that communicates research outcomes effectively to a scholarly audience.
10. **Feedback Interpretation**: Critically assess and respond to peer review feedback pertaining to a submitted research paper.
11. **Data Visualization**: Develop and explain a visual representation of research findings, emphasizing its significance to the study.
12. **Grant Proposal Draft**: Craft a draft grant proposal concentrating on the significance, innovation, and methodological approach of a proposed project.

## 5. Scoring Rubric
- **Usefulness (0-10 points)**: Evaluates the relevance and practicality of the assistance provided by the AI.
- **Correctness (0-10 points)**: Measures the accuracy of the content generated or analyzed.
- **Research Judgment (0-10 points)**: Assesses the depth of interpretation, critical thinking, and originality demonstrated in the research design or synthesis tasks.

## 6. Baselines for Comparison
- Performance benchmarks against human expert outputs on similar tasks.
- Existing AI systems that purport to assist in research tasks (e.g., ChatGPT and other academic-oriented AI applications).
- Evaluation outcomes from established benchmarks like AgentBench and PaperBench, adapted for research tasks.

## 7. Likely Failure Modes and Gaming Risks
- **Superficial Compliance**: AI systems might generate overly simplistic or generic responses that superficially fulfill task requirements without providing deeper insights.
- **Data Manipulation**: There’s a risk of AI systems reflecting biases inherent in training data, delivering results that lack factual accuracy.
- **Evasive Responses**: In adversarial settings, AI might sidestep challenges by providing vague or non-committal responses to complex questions.

## 8. Human Evaluation Protocol
- A selection panel of experienced researchers will carry out blind assessments of AI outputs.
- Evaluators will utilize structured forms aligned with the scoring rubric, ensuring consistent application across tasks.
- Qualitative feedback will be encouraged in tandem with quantitative scores to foster iterative improvements.

## 9. Limitations of the Benchmark
- The benchmark may not fully encapsulate the complexity and diversity of various academic disciplines and research methodologies.
- The quality of evaluation outcomes may be significantly affected by the prompts provided and the subjective interpretation of evaluators.
- Biases inherent in expert evaluations could influence human scoring based on individual expectations and domain expertise.

## 10. Recommendations for Version 2
- Expand the benchmark to accommodate a wider array of disciplines to enrich the diversity of evaluated tasks.
- Implement a mixed-methods evaluation that combines quantitative metrics with qualitative insights, enhancing interpretive depth.
- Increase the complexity of adversarial components to more effectively assess AI capabilities under challenging conditions.
- Explore scenarios requiring robust AI interaction with human agents or other AI systems, adding realism to task execution and evaluation.

This document serves as a foundational draft for discussion in the lab. Collaborative feedback will be invaluable in refining and optimizing the **ResearchAgentBench** framework to ensure it fulfills its intended role effectively. 

---

#### Sources
[1] Developing AI Agents for IT Automation Tasks with ITBench for AAAI 2026 - IBM Research - https://research.ibm.com/publications/developing-ai-agents-for-it-automation-tasks-with-itbench  
[2] AgentBench (AgentBench) - Agentic Design | Agentic Design Patterns - https://agentic-design.ai/patterns/evaluation-monitoring/agentbench  
[3] AgentBench, a comprehensive benchmark for evaluating AI agent performance, is now available! | AI-SCHOLAR | AI: (Artificial Intelligence) Articles and technical information media - https://ai-scholar.tech/en/articles/agent-simulation/agentbench  
[4] ICML Poster PaperBench: Evaluating AI’s Ability to Replicate AI Research - https://icml.cc/virtual/2025/poster/43586  
[5] PaperBench: Evaluating AI's Ability to Replicate AI Research | OpenAI - https://openai.com/index/paperbench

</details>

**Nguồn (multi-agent đã tìm và trích dẫn):**

1. [Developing AI Agents for IT Automation Tasks with ITBench for AAAI 2026 - IBM Research](https://research.ibm.com/publications/developing-ai-agents-for-it-automation-tasks-with-itbench) — # Developing AI Agents for IT Automation Tasks with ITBench. One such important and challenging area is that of addressing IT management tasks, including solving IT incidents, which often require extensive human expertise and effort. To enable the development of agents for these tasks, in this lab, we introduce ITBench, an open benchmark for IT automation that simulates realistic environments where agents interact with IT systems and multi-modal operational data, including logs, metrics, alerts, and traces. Together, they provide a testbed for benchmarking agentic systems across a host of critical challenges, such as planning and reasoning over massive and heterogeneous IT data, safety, and stochasticity in live IT systems. ITBench\_static is more beginner-friendly, enabling rapid benchmarking of agents against a smaller set of unique IT-domain challenges. ITBench\_live enables more advanced researchers and practitioners familiar with IT systems to develop and test their agents against the full suite of challenging IT problems. We will guide attendees to use both ITBench\_static and ITBench\_live to develop baseline multi-agent systems and benchmark their performance.
2. [AgentBench (AgentBench) - Agentic Design | Agentic Design Patterns](https://agentic-design.ai/patterns/evaluation-monitoring/agentbench) — The first comprehensive benchmark to evaluate LLMs as agents across 8 diverse environments, assessing reasoning and decision-making in multi-turn open-ended settings. **Pattern:** First comprehensive benchmark evaluating LLMs as agents across 8 diverse environments. **Why:** Systematic assessment of reasoning, decision-making, and multi-turn interaction capabilities in realistic settings. **Key Insight:** Reveals significant performance gaps between commercial and open-source models in complex agent tasks. ✅Test across all 8 environments for comprehensive evaluation. ✅Focus on long-term reasoning and decision-making capabilities. ### 🚦 When to Use. * • Comprehensive LLM agent capability assessment. * • Research on agent reasoning and decision-making. Aggregate performance across all 8 environments. Performance on extended reasoning tasks. LLM Agent Research: Comprehensive evaluation of reasoning and decision-making across diverse domains. Academic Research: Supporting publications on agent capabilities and multi-turn interaction quality. Agent Development: Guiding improvements in long-term reasoning and instruction following. AgentBench Dataset on Papers with CodeHugging Face Paper PageLLM Agent Benchmark Comparison ListAI Agent Benchmarks Overview (Evidently AI). ## Design Patterns & Techniques.
3. [AgentBench, a comprehensive benchmark for evaluating AI agent performance, is now available! | AI-SCHOLAR | AI: (Artificial Intelligence) Articles and technical information media](https://ai-scholar.tech/en/articles/agent-simulation/agentbench) — AgentBench, A Comprehensive Benchmark For Evaluating AI Agent Performance, Is Now Available! ******3 main points******✔️ Proposed AgentBench, a comprehensive benchmark for evaluating agents generated by large-scale language models. To **address these issues and evaluate the performance of agents generated by LLM, this paper proposes AgentBench, a comprehensive benchmark consisting of eight tasks and environments based on real-world scenarios and 25 different** The **paper** describes a **large-scale comparative experiment using LLM agents**. AgentBench is a tool that allows LLM-generated agents to interact with an **Operating System (OS),****Database (DB),****Knowledge Graph (KG),****Digital Card Game (DCG),****Lateral** Thinking Puzzles (LTP), House-holding (HH), Web Shopping (WS), and Web Browsing (WB) based on a real-world scenario. In this article, we described a paper that proposed AgentBench, a comprehensive benchmark composed of 8 tasks and environments based on real-world scenarios to evaluate the performance of agents generated by LLM, and conducted a large-scale comparison experiment using 25 different LLM agents, including API-based and open source models.
4. [ICML Poster PaperBench: Evaluating AI’s Ability to Replicate AI Research](https://icml.cc/virtual/2025/poster/43586) — # PaperBench: Evaluating AI’s Ability to Replicate AI Research. We introduce PaperBench, a benchmark evaluating the ability of AI agents to replicate state-of-the-art AI research. Our work introduces PaperBench, a benchmark that challenges AI systems to replicate 20 cutting-edge machine learning papers completely from scratch, requiring them to understand the research, write code, and successfully run experiments. We developed detailed assessment rubrics with the original paper authors to break down each replication task into hundreds of individually gradable components, turning a complex subjective evaluation into an objective assessment that can be automatically graded by other AI systems. When testing several advanced AI systems, we found that even the best-performing AI agent could only achieve a replication score of 27%, while human machine learning experts scored 41% under similar circumstances.We release PaperBench to provide a valuable tool for measuring how well AI systems can autonomously perform complex machine learning research, helping track progress as these capabilities advance and informing important decisions about AI development and governance.
5. [PaperBench: Evaluating AI's Ability to Replicate AI Research | OpenAI](https://openai.com/index/paperbench) — # PaperBench: Evaluating AI’s Ability to Replicate AI Research | OpenAI. *   Foundation(opens in a new window). Log inTry ChatGPT(opens in a new window). Evaluating AI’s Ability to Replicate AI Research. Read paper(opens in a new window)View code(opens in a new window). We introduce PaperBench, a benchmark evaluating the ability of AI agents to replicate state-of-the-art AI research. We open-source⁠(opens in a new window) our code to facilitate future research in understanding the AI engineering capabilities of AI agents. *   ChatGPT(opens in a new window). *   ChatGPT Business(opens in a new window). *   ChatGPT Enterprise(opens in a new window). *   ChatGPT for Education(opens in a new window). *   API Log In(opens in a new window). *   Docs(opens in a new window). *   Resources(opens in a new window). (opens in a new window)(opens in a new window)(opens in a new window)(opens in a new window)(opens in a new window)(opens in a new window)(opens in a new window).

