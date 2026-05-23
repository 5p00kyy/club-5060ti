# Benchmarks

Benchmarks here are receipts, not universal claims. Always include the setup details needed to reproduce them.

Fresh seed results are stored as schema-validated JSON under data/results/ and rendered through the hosted explorer at https://5p00kyy.github.io/club-5060ti/. Imported llm-bench rows are archived historical data and should be redone before comparison use.

The explorer defaults to one card per model/setup, with prompt-specific benchmark rows inside each card. Repeated runs are collapsed to the highest-generation row for each prompt while keeping averages and the run count visible. MTP/speculation, hardware lane, thinking mode, and reasoning budget are shown on each card.

## 2026-05-19 Focused Seed Data

Current headline benchmark files:

- data/results/seed-qwen35-9b-mtp-1x5060ti-20260519.json
- data/results/seed-qwen35-9b-nomtp-1x5060ti-20260519.json
- data/results/seed-qwen36-27b-iq4xs-1x5060ti-20260519.json
- data/results/seed-qwen36-27b-q3kxl-1x5060ti-20260519.json
- data/results/seed-qwen36-35b-a3b-iq3xxs-1x5060ti-20260519.json
- data/results/seed-qwen-mtp-2x5060ti-20260519.json
- data/results/seed-qwen36-35b-a3b-2x5060ti-20260519.json
- data/results/seed-beellama-qwen36-27b-20260523.json

Archived provenance:

- data/results/llm-bench-legacy-import.json

Best decode results by lane, model, and prompt:

| Lane | Model | Quant | Prompt set | Thinking | Reasoning budget | Speculation | Best generation tok/s | Generated tokens |
| --- | --- | --- | --- | --- | ---: | --- | ---: | ---: |
| 1x5060ti | Qwen3.5-9B | UD-Q4_K_XL | short-chat | off |  | draft-mtp n=2 | 82.16 | 256 |
| 1x5060ti | Qwen3.5-9B | UD-Q4_K_XL | code-generate | off |  | draft-mtp n=2 | 96.25 | 768 |
| 1x5060ti | Qwen3.5-9B | UD-Q4_K_XL | agent-tool | off |  | draft-mtp n=2 | 77.31 | 512 |
| 1x5060ti | Qwen3.5-9B | UD-Q4_K_XL | long-retrieval | off |  | draft-mtp n=2 | 77.41 | 17 |
| 1x5060ti | Qwen3.5-9B | UD-Q4_K_XL | short-chat | off |  | no MTP | 63.32 | 256 |
| 1x5060ti | Qwen3.5-9B | UD-Q4_K_XL | code-generate | off |  | no MTP | 63.31 | 768 |
| 1x5060ti | Qwen3.5-9B | UD-Q4_K_XL | agent-tool | off |  | no MTP | 63.28 | 512 |
| 1x5060ti | Qwen3.5-9B | UD-Q4_K_XL | long-retrieval | off |  | no MTP | 57.90 | 17 |
| 1x5060ti | Qwen3.6-27B | IQ4_XS | short-chat | off |  | no MTP | 24.66 | 256 |
| 1x5060ti | Qwen3.6-27B | IQ4_XS | code-generate | off |  | no MTP | 24.57 | 768 |
| 1x5060ti | Qwen3.6-27B | IQ4_XS | agent-tool | off |  | no MTP | 24.59 | 512 |
| 1x5060ti | Qwen3.6-27B | IQ4_XS | long-retrieval | off |  | no MTP | 22.26 | 17 |
| 1x5060ti | Qwen3.6-27B | UD-Q3_K_XL | short-chat | off |  | no MTP | 22.76 | 256 |
| 1x5060ti | Qwen3.6-27B | UD-Q3_K_XL | code-generate | off |  | no MTP | 22.68 | 768 |
| 1x5060ti | Qwen3.6-27B | UD-Q3_K_XL | agent-tool | off |  | no MTP | 22.67 | 512 |
| 1x5060ti | Qwen3.6-27B | UD-Q3_K_XL | long-retrieval | off |  | no MTP | 20.70 | 17 |
| 1x5060ti | Qwen3.6-27B | UD-Q3_K_XL | short-chat | off |  | DFlash n=16 | 43.49 | 256 |
| 1x5060ti | Qwen3.6-27B | UD-Q3_K_XL | code-generate | off |  | DFlash n=16 | 69.34 | 768 |
| 1x5060ti | Qwen3.6-27B | UD-Q3_K_XL | agent-tool | off |  | DFlash n=16 | 34.85 | 512 |
| 1x5060ti | Qwen3.6-35B-A3B | IQ3_XXS | short-chat | on | 384 | no MTP | 94.63 | 640 |
| 1x5060ti | Qwen3.6-35B-A3B | IQ3_XXS | code-generate | on | 384 | no MTP | 94.46 | 1152 |
| 1x5060ti | Qwen3.6-35B-A3B | IQ3_XXS | agent-tool | on | 384 | no MTP | 94.53 | 896 |
| 1x5060ti | Qwen3.6-35B-A3B | IQ3_XXS | long-retrieval | on | 384 | no MTP | 75.89 | 191 |
| 2x5060ti | Qwen3.5-9B | UD-Q4_K_XL | short-chat | off |  | draft-mtp n=3 | 69.43 | 256 |
| 2x5060ti | Qwen3.5-9B | UD-Q4_K_XL | code-generate | off |  | draft-mtp n=3 | 88.64 | 768 |
| 2x5060ti | Qwen3.5-9B | UD-Q4_K_XL | agent-tool | off |  | draft-mtp n=3 | 70.89 | 512 |
| 2x5060ti | Qwen3.5-9B | UD-Q4_K_XL | long-retrieval | off |  | draft-mtp n=3 | 102.42 | 17 |
| 2x5060ti | Qwen3.6-27B | UD-Q4_K_XL | short-chat | off |  | draft-mtp n=3 | 34.11 | 256 |
| 2x5060ti | Qwen3.6-27B | UD-Q4_K_XL | code-generate | off |  | draft-mtp n=3 | 37.66 | 768 |
| 2x5060ti | Qwen3.6-27B | UD-Q4_K_XL | agent-tool | off |  | draft-mtp n=3 | 28.95 | 512 |
| 2x5060ti | Qwen3.6-27B | UD-Q4_K_XL | long-retrieval | off |  | draft-mtp n=3 | 38.37 | 17 |
| 2x5060ti | Qwen3.6-35B-A3B | UD-IQ4_XS | short-chat | on | 384 | no MTP | 90.10 | 640 |
| 2x5060ti | Qwen3.6-35B-A3B | UD-IQ4_XS | code-generate | on | 384 | no MTP | 89.79 | 1152 |
| 2x5060ti | Qwen3.6-35B-A3B | UD-IQ4_XS | agent-tool | on | 384 | no MTP | 89.64 | 896 |
| 2x5060ti | Qwen3.6-35B-A3B | UD-IQ4_XS | long-retrieval | on | 384 | no MTP | 70.33 | 172 |

Long-retrieval rows use a synthetic filler prompt and short-answer retrieval target. Treat them as long-prompt fit/retrieval checks, not sustained decode benchmarks.

## Single-GPU Presets

Current single-card examples:

- examples/llamacpp-single-5060ti.ini - Qwen3.5 9B high-context MTP and no-MTP presets.
- examples/llamacpp-single-5060ti-qwen36-27b-q3kxl.ini - Qwen3.6 27B Q3_K_XL no-MTP presets at 204800 and 262144 q8 KV.
- examples/llamacpp-single-5060ti-qwen36-27b-iq4xs.ini - Qwen3.6 27B IQ4_XS no-MTP preset at 32768 q8 KV.
- examples/llamacpp-single-5060ti-qwen36-35b-a3b-iq3xxs.ini - Qwen3.6 35B A3B IQ3_XXS thinking presets at 204800 and native max context.

Qwen3.6 27B MTP Q4_XL is not currently a valid one-card GPU-only preset on this seed system because the model allocation fails on a single 16GB card. The current useful one-card MTP/no-MTP comparison is Qwen3.5 9B. For high-context 27B on one card, the current clean route is Q3_K_XL with q8 KV rather than lowering the KV cache precision on the larger IQ4_XS file.

## Current Comparison Gaps

- Qwen3.6 27B no-MTP on 2x5060ti with the same quant/context as the MTP route, if a clean non-MTP route is available.
- BeeLlama DFlash needs more sweeps before promotion beyond exploratory rows. The first clean result is single-card Q3_K_XL at 8K; dual-card Q4_K_M DFlash failed with drafter KV-position errors.
- Qwen3.6 35B A3B NVFP4/MTP belongs in a separate vLLM engine lane, not mixed into the llama.cpp GGUF rows.
- Reasoning-budget sweeps for Qwen3.6 35B A3B should be added as quality/latency rows once the baseline speed data is stable.
- Community multi-card submissions should start with the same prompt sets and schema fields so 3x/4x results can sit beside the 1x and 2x lanes.

## Benchmark Hygiene

When adding results, say whether tokens/sec is decode-only or end-to-end, include generated token count, prompt/context size, runtime version, quant, KV cache dtype, MTP/speculative settings, thinking mode, and reasoning budget.
