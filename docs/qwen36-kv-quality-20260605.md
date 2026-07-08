# Qwen3.6 KV Cache Quality Proof - 2026-06-05

This note captures a small quality-proof pass for the Qwen3.6 KV-cache comparison rows. It is not a broad model-quality benchmark. It is a reproducible sanity check that the speed rows did not hide obvious failures on retrieval, strict structure, sensitive-data handling, or code-shaped output.

## Setup

Seed hardware:

- Lane: 2x RTX 5060 Ti 16GB
- Runtime: upstream llama.cpp `9518` / `7c158fbb4`
- Context: 32768 tokens
- Thinking: off
- Prompt harness: `scripts/run_quality_proof.py`

Compared setups:

| Setup | Model file class | KV cache | Speculation |
| --- | --- | --- | --- |
| Qwen3.6 27B | Q6_K_XL | f16 / f16 | draft-MTP n=3 |
| Qwen3.6 27B | Q6_K_XL | q8_0 / q8_0 | draft-MTP n=3 |
| Qwen3.6 27B | Q6_K_XL | q4_0 / q4_0 | draft-MTP n=3 |
| Qwen3.6 35B-A3B | Q5_K_S | f16 / f16 | none |

## Prompt Checks

The harness runs four deterministic checks:

- `long_needle`: retrieve `CLUB-5060TI-NEEDLE-194` from a roughly 30K-token synthetic prompt.
- `strict_json`: return exactly the requested minified JSON shape and values.
- `instruction_conflict`: avoid repeating untrusted sensitive placeholder values and describe redaction/omission behavior.
- `code_sanity`: emit a plausible `slugify_result_id(value: str) -> str` function with asserts and fallback behavior.

Each checked output is stored as a short sanitized excerpt in `data/quality/`.

## Results

| Setup | Passes | Needle wall | Needle prompt tok/s | Code wall | Code decode tok/s |
| --- | ---: | ---: | ---: | ---: | ---: |
| 27B Q6 f16 KV | 4 / 4 | 41.45s | 732.93 | 13.33s | 25.47 |
| 27B Q6 q8 KV | 4 / 4 | 41.74s | 728.05 | 13.47s | 25.10 |
| 27B Q6 q4 KV | 4 / 4 | 41.69s | 728.94 | 12.72s | 26.71 |
| 35B-A3B Q5 f16 KV | 4 / 4 | 15.41s | 1996.99 | 1.97s | 123.51 |

Artifacts:

- `data/quality/seed-qwen36-27b-q6-f16kv32k-quality-20260605.json`
- `data/quality/seed-qwen36-27b-q6-q8kv32k-quality-20260605.json`
- `data/quality/seed-qwen36-27b-q6-q4kv32k-quality-20260605.json`
- `data/quality/seed-qwen36-35b-a3b-q5-f16kv32k-quality-20260605.json`

## Interpretation

At this 32K context tier, the 27B Q6 f16/q8/q4 KV variants all passed the same quality proof and showed similar long-prompt retrieval timing. This does not prove q4 KV is always safe; it only means this small proof set did not expose a q4-specific failure.

The 35B-A3B Q5 f16 KV row is the stronger practical lead from this pass. It passed the same checks while running much faster on both the long-prompt retrieval prefill and code-shaped output. Because the 35B-A3B row uses a MoE active-parameter route and no MTP while the 27B rows use dense 27B with draft-MTP, treat this as a recipe comparison rather than a pure model-size or KV-cache comparison.

## Caveats

- Single run per setup.
- The long-needle check is a short-answer retrieval proof, not sustained decode.
- The prompt set is intentionally small and deterministic; it is not a substitute for real coding-agent or long-session evaluation.
- The 65K and 186K f16 GGUF routes were too heavy for quick direct benchmarking in this pass and are not promoted here.
