# Design Template

## Problem

Xây dựng một research assistant nhận một câu hỏi nghiên cứu dài (ví dụ: "Research GraphRAG
state-of-the-art and write a 500-word summary"), tự động tìm nguồn, phân tích thông tin, và
viết câu trả lời cuối cùng có trích dẫn nguồn — đồng thời đo được latency/cost/quality để so
sánh với cách làm single-agent.

## Why multi-agent?

Single-agent (một lần gọi LLM duy nhất) không tách được các bước "tìm nguồn" → "phân tích" →
"viết", nên không kiểm soát được nguồn dữ liệu dùng để trả lời, khó audit từng bước, và dễ trộn
lẫn việc tìm kiếm với việc viết khiến output thiếu trích dẫn rõ ràng. Multi-agent tách rõ
trách nhiệm theo từng agent, cho phép trace từng bước và đo chất lượng riêng của từng giai đoạn
(citation coverage, source count) — điều baseline không cung cấp được.

## Agent roles

| Agent | Responsibility | Input | Output | Failure mode |
|---|---|---|---|---|
| Supervisor | Quyết định route kế tiếp (researcher/analyst/writer/done) và enforce guardrail | `ResearchState` hiện tại | `state.next_route`, `state.route_history` | Loop vô hạn nếu không enforce `max_iterations` |
| Researcher | Tìm nguồn và tóm tắt thành research notes | `request.query` | `state.sources`, `state.research_notes` | Search trả về rỗng/không liên quan |
| Analyst | Rút key claims, so sánh viewpoint, flag evidence yếu | `state.research_notes`, `state.sources` | `state.analysis_notes` | Bỏ sót mâu thuẫn giữa nguồn |
| Writer | Tổng hợp câu trả lời cuối có trích dẫn | `state.research_notes`, `state.analysis_notes` | `state.final_answer` | Thiếu trích dẫn hoặc trả lời quá ngắn |

## Shared state

`ResearchState` (`core/state.py`) là nguồn sự thật duy nhất truyền qua các agent:

- `request`: câu hỏi gốc — mọi agent cần để giữ ngữ cảnh.
- `iteration` / `route_history`: đếm bước đã chạy — guardrail chống loop vô hạn.
- `next_route`: quyết định mới nhất của Supervisor — workflow đọc để dispatch.
- `sources` / `research_notes` / `analysis_notes` / `final_answer`: handoff output giữa các agent.
- `agent_results`: lưu output + metadata (token, cost) từng agent — phục vụ benchmark.
- `trace` / `errors`: phục vụ debug và fallback khi một agent fail.

## Routing policy

```text
Supervisor kiểm tra theo thứ tự:
  iteration >= max_iterations            -> done (guardrail)
  research_notes is None                 -> researcher
  research_notes set, analysis_notes None -> analyst
  analysis_notes set, final_answer None   -> writer
  final_answer set                        -> done
```

## Guardrails

- Max iterations: `Settings.max_iterations` (mặc định 8) — Supervisor ép `done` khi vượt ngưỡng;
  đủ chỗ cho 1 vòng đầy đủ (researcher→analyst→writer→critic) + 1 lần Writer sửa lại theo
  feedback của Critic (`Settings.max_revisions`, mặc định 1).
- Timeout: `Settings.timeout_seconds` (mặc định 60) — dự kiến áp ở tầng gọi LLM/search.
- Retry: `LLMClient` dùng `tenacity` retry 3 lần với exponential backoff cho mỗi lần gọi.
- Fallback: nếu một worker raise exception, workflow ghi lỗi vào `state.errors` và dừng vòng lặp
  thay vì crash toàn bộ chương trình.
- Validation: input/output giữa các tầng đều là Pydantic schema (`core/schemas.py`).

## Benchmark plan

| Query | Metric | Expected outcome |
|---|---|---|
| "Research GraphRAG state-of-the-art and write a 500-word summary" | Latency, cost, quality, citation coverage | Multi-agent có citation coverage cao hơn baseline nhờ tách bước research riêng |
| "Compare single-agent and multi-agent workflows for customer support" | Latency, error rate | Multi-agent latency cao hơn (nhiều LLM call) nhưng error rate thấp hơn nhờ guardrail |
| "Summarize production guardrails for LLM agents" | Quality score | Multi-agent quality score cao hơn nhờ bước Analyst lọc evidence yếu |
