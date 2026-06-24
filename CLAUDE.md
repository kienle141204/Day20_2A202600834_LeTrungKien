# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A **teaching starter skeleton** for a multi-agent research system (Supervisor + Researcher + Analyst + Writer, benchmarked against a single-agent baseline). Core logic is intentionally left unimplemented and raises `StudentTodoError`. **Do not "complete" these TODOs unless explicitly asked** — empty/raising implementations are by design, and the tests assert that they raise. Find them with:

```bash
grep -R "TODO(student)" -n src tests docs
```

## Commands

```bash
make install      # pip install -e "[dev,llm]" — installs dev + optional LLM deps
make test         # pytest (config in pyproject: pythonpath=src, testpaths=tests)
make lint         # ruff check src tests
make format       # ruff format src tests
make typecheck    # mypy src (strict mode)

pytest tests/test_state.py::test_name   # run a single test
```

Run the CLI (entrypoints: `malab` or `python -m multi_agent_research_lab.cli`):

```bash
python -m multi_agent_research_lab.cli baseline --query "..."      # minimal placeholder, returns canned text
python -m multi_agent_research_lab.cli multi-agent --query "..."   # exits code 2 (StudentTodoError) until implemented
```

Note: `make install` and Makefile `pip install -e "[dev,llm]"` rely on shell brace-expansion semantics; the README's `pip install -e "[dev]"` is the documented dev-only variant. Requires Python >=3.11.

## Architecture

State flows through one Pydantic object, `ResearchState` (`core/state.py`), which is the single source of truth passed between agents. Agents read from and mutate it, then return it. Key fields: `request`, `iteration`/`route_history` (loop guards), `research_notes`/`analysis_notes`/`final_answer` (handoff outputs), `agent_results`/`trace`/`errors` (observability).

Layer boundaries (keep them):
- **`agents/`** — each agent subclasses `BaseAgent` (`agents/base.py`) and implements `run(state) -> state`. Agent *internals* live here.
- **`graph/workflow.py`** — `MultiAgentWorkflow` owns *orchestration* (LangGraph nodes/edges/routing/stop conditions). Keep routing here, not in agents.
- **`core/`** — `config.py` (Pydantic-settings `Settings`, accessed only via cached `get_settings()`), `schemas.py` (all cross-layer Pydantic models + `AgentName`/`AgentResult`), `state.py`, `errors.py`.
- **`services/`** — external I/O clients (LLM, search, storage). Agents call services; they never read env vars directly.
- **`evaluation/`** — benchmark single vs multi-agent (`BenchmarkMetrics`: latency/cost/quality).
- **`observability/`** — logging + tracing hooks.

Conventions enforced by the skeleton: all cross-boundary I/O uses Pydantic schemas from `core/schemas.py`; config is read only through `get_settings()` (never `os.environ` in agents); guardrails come from `Settings.max_iterations` / `timeout_seconds`. mypy runs in **strict** mode and ruff selects `E,F,I,B,UP,SIM` — new code must satisfy both.

## Errors

`core/errors.py` defines the hierarchy under `LabError`: `StudentTodoError` (unimplemented learner code — the CLI catches it and exits 2), `AgentExecutionError` (failure after retries/fallbacks), `ValidationError`.
