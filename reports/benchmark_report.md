# Benchmark Report

| Run | Latency (s) | Cost (USD) | Quality | Citation cov. | Failure rate | Notes |
|---|---:|---:|---:|---:|---:|---|
| baseline | 43.14 |  | 5.0 | 0% | 0% | Gemini usage recorded; provider cost unavailable; quality proxy |
| multi-agent | 0.30 | 0.0000 | 10.0 | 100% | 0% | single-query quality proxy; replace with peer-review score |

## Experiment context

- Query: `Research GraphRAG state-of-the-art and write a 500-word summary`.
- Baseline used Google AI Studio model `models/gemini-3.6-flash` successfully.
- Google returned HTTP 503 once; the configured retry then received HTTP 200.
- Multi-agent workers used the same local corpus with deterministic offline processing.
- Gemini did not return a billing amount, so baseline cost is left blank rather than reported as zero.

## LangSmith trace evidence

Project: `multi-agent-research-lab`

| Agent | Run ID | Status |
|---|---|---|
| Researcher | `01a01edd-3846-74b0-bcc9-f9f0a85eae21` | success |
| Analyst | `01a01edd-395f-7531-adb2-cfaf680be362` | success |
| Writer | `01a01edd-3961-7082-b7ca-2c33d402fef5` | success |

## Analysis

- Fastest run: **multi-agent** (0.30s).
- Highest quality proxy: **multi-agent** (10.0/10).
- Quality is an offline heuristic; add peer-review scores for submission.
- Multi-agent adds handoff/token overhead; use it when decomposition or independent verification creates measurable value.

## Failure mode and mitigation

An unsupported claim can propagate through shared state and look like consensus. Keep source IDs at handoffs, validate citations, cap iterations, and inspect the JSON traces before accepting the final answer.

## Peer review pending

The quality values above are automated proxies. A classmate should complete the rubric and
record the reviewer name, feedback, and final score before submission.
