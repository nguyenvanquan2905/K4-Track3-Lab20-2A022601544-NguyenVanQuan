# Multi-Agent Research System Design

## Problem

Hệ thống nhận một câu hỏi nghiên cứu dài, truy xuất tối đa năm tài liệu trong corpus
offline, phân tích bằng chứng và tạo câu trả lời có citation. Cùng câu hỏi được chạy qua
single-agent baseline và multi-agent workflow để so sánh định lượng.

## Why multi-agent?

Một agent phù hợp với câu hỏi ngắn, nhưng nhiệm vụ nghiên cứu dài có ba loại công việc
khác nhau: thu thập nguồn, kiểm tra/đối chiếu bằng chứng và trình bày. Việc tách vai trò
giúp trace từng artifact và phát hiện lỗi handoff. Lợi ích này phải được đối chiếu với độ
trễ, chi phí và rủi ro lỗi lan truyền trong benchmark.

## Agent roles

| Agent | Responsibility | Input | Output | Failure mode |
|---|---|---|---|---|
| Supervisor | Chọn bước kế tiếp và dừng workflow | Toàn bộ shared state | `route_history` | Lặp vô hạn; chặn bằng `max_iterations` |
| Researcher | Xếp hạng corpus và giữ provenance | Query, `max_sources` | `sources`, `research_notes` | Không tìm thấy nguồn hoặc nguồn yếu |
| Analyst | Rút claim, nêu giới hạn bằng chứng | Sources và research notes | `analysis_notes` | Lặp lại claim không được hỗ trợ |
| Writer | Viết câu trả lời có citation | Analysis và sources | `final_answer` | Citation thiếu hoặc không khớp claim |

## Shared state

- `request`: query, audience và giới hạn nguồn.
- `sources`: tài liệu có title, URI, snippet và metadata provenance.
- `research_notes`, `analysis_notes`, `final_answer`: artifact rõ ràng cho từng handoff.
- `iteration`, `route_history`: phục vụ routing và chống vòng lặp.
- `agent_results`, `trace`, `errors`: quan sát, benchmark và debug.

## Routing policy

`missing sources -> researcher -> missing analysis -> analyst -> missing answer -> writer -> done`.
Supervisor chạy lại sau mỗi worker. Khi đạt `max_iterations` hoặc timeout, workflow ghi lỗi
và dừng an toàn.

## Guardrails

- Max iterations: 6 mặc định, cấu hình qua `MAX_ITERATIONS`.
- Timeout: 60 giây mặc định, cấu hình qua `TIMEOUT_SECONDS`.
- Retry/fallback: OpenAI client dùng 2 retry; thiếu key hoặc SDK thì fallback offline.
- Validation: Pydantic kiểm tra query, source và metric; critic kiểm tra citation coverage.
- Provenance: mọi nguồn offline mang URI và đường dẫn corpus trong metadata.

## Benchmark plan

Chạy cùng query qua baseline và multi-agent. Đo wall-clock latency, estimated token cost,
quality proxy 0–10, citation coverage và failure rate. Kết quả tự động được ghi vào
`reports/benchmark_report.md`; hai JSON trace dùng làm bằng chứng tái lập. Quality proxy
chỉ dùng cho smoke test và phải được bổ sung điểm peer review khi nộp chính thức.

## Exit ticket

Nên dùng multi-agent khi bài toán có thể phân rã thành các bước cần chuyên môn hoặc kiểm
chứng độc lập và benchmark chứng minh chất lượng tăng đáng kể. Không nên dùng khi query
ngắn, bằng chứng đã có sẵn hoặc coordination overhead lớn hơn lợi ích chất lượng.
