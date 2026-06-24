# Plan triển khai Multi-Agent Research Lab

Repo này là **teaching skeleton**: mọi logic lõi từng `raise StudentTodoError`. File này liệt kê
toàn bộ nhiệm vụ và trạng thái hoàn thành.

**Quyết định thiết kế đã chốt:**
- LLM + Search dùng **mock deterministic** (chạy không cần API key), có seam để cắm OpenAI/Tavily
  thật sau (đọc `OPENAI_API_KEY`/`TAVILY_API_KEY` từ `.env`).
- Orchestration dùng **plain Python** (không LangGraph), tự viết vòng lặp Supervisor → worker.
- Hỗ trợ chạy trên **Python 3.10+** (thêm shim `StrEnum` cho < 3.11 trong `core/schemas.py`,
  hạ `requires-python`/`ruff target-version`/`mypy python_version` xuống `3.10`).

---

## Nhiệm vụ (13 marker `TODO(student)`) — TẤT CẢ ĐÃ HOÀN THÀNH

### A. Services
- [x] `services/llm_client.py` → `LLMClient.complete` — mock deterministic backend + seam OpenAI.
- [x] `services/search_client.py` → `SearchClient.search` — mock deterministic backend + seam Tavily.

### B. Agents
- [x] `SupervisorAgent.run` — routing theo field còn thiếu, guardrail `max_iterations`.
- [x] `ResearcherAgent.run` — search + tóm tắt → `research_notes`.
- [x] `AnalystAgent.run` — rút key claims → `analysis_notes`.
- [x] `WriterAgent.run` — tổng hợp → `final_answer`.
- [x] `CriticAgent.run` — kiểm tra citation/length cơ bản.

### C. Orchestration
- [x] `graph/workflow.py` → `build` + `run` (plain Python loop, có fallback khi worker lỗi).
- [x] `cli.py baseline` — single-agent thật (1 lần LLM).
- [x] `cli.py benchmark` (mới) — chạy baseline + multi-agent, sinh `reports/benchmark_report.md`.

### D. Evaluation + Observability
- [x] `evaluation/benchmark.py` → `run_benchmark` — thêm cost/quality/citation coverage/error rate.
- [x] `evaluation/report.py` → `render_markdown_report` — thêm section so sánh single vs multi.
- [x] `observability/tracing.py` → `trace_span` — thêm `start_ts` + sink module-level.

### E. Docs + scaffolding
- [x] `docs/design_template.md` — điền đầy đủ.
- [x] `docs/lab_guide.md` — đánh dấu các milestone đã hoàn thành.
- [x] `.env` — tạo từ `.env.example`.
- [x] `plan.md` — file này.
- [x] `reports/benchmark_report.md` — đã sinh thật từ `cli benchmark`.

## Thay đổi ngoài TODO
- [x] `core/state.py`: thêm `next_route: str | None = None`.
- [x] `core/schemas.py`: thêm `StrEnum` shim cho Python 3.10.
- [x] `pyproject.toml`: `requires-python = ">=3.10"`, ruff `target-version = "py310"`,
      mypy `python_version = "3.10"`, mypy override `ignore_missing_imports` cho `tavily.*`.
- [x] `tests/test_agents_todo.py`: thay test "raise StudentTodoError" bằng test hành vi thật.
- [x] Tests mới: `test_llm_client.py`, `test_search_client.py`, `test_workflow.py`, `test_benchmark.py`.

## Verification — ĐÃ CHẠY THẬT, KẾT QUẢ PASS

Chạy trong conda env `ai20k` (Python 3.10.20):

- `pytest` → **13 passed**. (Lưu ý môi trường: env này có `deepeval`/`ollama` cài global tự đăng ký
  pytest plugin và lỗi `SSL_CERT_FILE` khi autoload — không liên quan tới project. Workaround:
  `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest`.)
- `ruff check src tests` → **All checks passed!**
- `mypy src` (strict) → **Success: no issues found in 27 source files**.
- `python -m multi_agent_research_lab.cli baseline --query "..."` → in `final_answer` thật, exit 0.
- `python -m multi_agent_research_lab.cli multi-agent --query "..."` → route đầy đủ
  `researcher → analyst → writer → done`, JSON state có research/analysis/final_answer/trace,
  `errors: []`, exit 0.
- `python -m multi_agent_research_lab.cli benchmark --query "..."` → sinh
  `reports/benchmark_report.md` so sánh baseline vs multi-agent (latency/cost/quality delta).
- `bash scripts/check_todos.sh` → không còn `TODO(student)` ở bất kỳ đâu trong repo.
