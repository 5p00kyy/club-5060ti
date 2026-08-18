# Benchmarks

Benchmarks here are receipts, not universal claims. Always include the setup details needed to reproduce them.

Fresh seed results are stored as schema-validated JSON under data/results/ and rendered through the hosted explorer at https://5p00kyy.github.io/club-5060ti/. Imported llm-bench rows are archived historical data and should be redone before comparison use.

The explorer defaults to one card per model/setup, with prompt-specific benchmark rows inside each card. Repeated runs are collapsed to the highest-generation row for each prompt while keeping averages and the run count visible. MTP/speculation, hardware lane, thinking mode, and reasoning budget are shown on each card.

Quality-proof artifacts for the 2026-06-05 Qwen3.6 KV-cache comparison live under `data/quality/`; see `docs/qwen36-kv-quality-20260605.md`. These are small pass/fail checks beside the speed rows, not headline benchmark rows.

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
- data/results/seed-beellama-qwen36-35b-a3b-dflash-20260523.json

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
| 1x5060ti | Qwen3.6-35B-A3B | IQ3_XXS | short-chat | off |  | DFlash n=16 | 96.07 | 256 |
| 1x5060ti | Qwen3.6-35B-A3B | IQ3_XXS | code-generate | off |  | DFlash n=16 | 138.26 | 768 |
| 1x5060ti | Qwen3.6-35B-A3B | IQ3_XXS | agent-tool | off |  | DFlash n=16 | 98.24 | 512 |
| 1x5060ti | Qwen3.6-35B-A3B | IQ3_XXS | long-retrieval | off |  | DFlash n=16 | 38.24 | 17 |
| 1x5060ti | Qwen3.6-35B-A3B | IQ3_XXS | short-chat | off |  | no MTP | 89.36 | 256 |
| 1x5060ti | Qwen3.6-35B-A3B | IQ3_XXS | code-generate | off |  | no MTP | 89.20 | 768 |
| 1x5060ti | Qwen3.6-35B-A3B | IQ3_XXS | agent-tool | off |  | no MTP | 88.73 | 512 |
| 1x5060ti | Qwen3.6-35B-A3B | IQ3_XXS | long-retrieval | off |  | no MTP | 58.99 | 17 |
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
| 2x5060ti | Qwen3.6-27B | UD-Q6_K_XL | custom (long-context-generate) | off |  | draft-mtp n=3 | 21.73 | 742 |
| 2x5060ti | Qwen3.6-35B-A3B | UD-IQ4_XS | short-chat | on | 384 | no MTP | 90.10 | 640 |
| 2x5060ti | Qwen3.6-35B-A3B | UD-IQ4_XS | code-generate | on | 384 | no MTP | 89.79 | 1152 |
| 2x5060ti | Qwen3.6-35B-A3B | UD-IQ4_XS | agent-tool | on | 384 | no MTP | 89.64 | 896 |
| 2x5060ti | Qwen3.6-35B-A3B | UD-IQ4_XS | long-retrieval | on | 384 | no MTP | 70.33 | 172 |

Long-retrieval rows use a synthetic filler prompt and short-answer retrieval target. Treat them as long-prompt fit/retrieval checks, not sustained decode benchmarks.
For sustained long-context decode in the 2x5060ti Qwen3.6-27B lane, use the `custom (long-context-generate)` row with `87293` prompt tokens and `742` generated tokens as the practical 96K-class reference. Follow-up 150K+ prompt-token diagnostics could prefill, but decode fell below 1 tok/s, so those runs are not promoted as useful benchmark results.

## 2026-08-17 Qwen3.8 vLLM NVFP4

The recommended vLLM profile uses two cards, 122,880 context, FP8 KV, MTP n=3, a 2,048-token prefill chunk, one sequence, and an explicit 2,500,000,000-byte KV allocation per GPU.

Three consecutive 118,660-prompt-token, 512-output-token runs produced 952.18–953.01 tok/s prefill (952.50 median) and 66.99–67.41 tok/s decode (67.29 median). A tool-call schema gate and a three-marker 49,125-token retrieval gate passed. Larger 4,096-token chunks repeatedly OOMed under real load and are not published as a preset. See `docs/vllm-qwen38.md` and `data/results/seed-qwen38-27b-nvfp4-vllm-2x5060ti-20260817.json`.

## 2026-08-18 Qwen3.8 matched stack quality — V2

The matched V2 68-case run reports separate measures: vLLM NVFP4/FP8-KV/MTP3 reached **65/68 answer-correct**, **64/68 completion-contract**, and **61/68 combined exact-contract**; llama.cpp Q6_K/f16-KV/draft-MTP2 reached **66/68**, **68/68**, and **66/68** respectively. Both stacks were answer-correct on all 10 long-context marker checks at closely matched actual prompt-token counts. See the [comparison note](qwen38-stack-quality-comparison-20260818.md) and [compact V2 evidence](../data/quality/seed-qwen38-stack-comparison-quality-20260818.json). This is complete serving-stack evidence, not quantization-only proof; the bounded caps and contracts make it a regression signal, not a broad model-quality score.

## Single-GPU Presets

Current single-card examples:

- examples/llamacpp-single-5060ti.ini - Qwen3.5 9B high-context MTP and no-MTP presets.
- examples/llamacpp-single-5060ti-qwen36-27b-q3kxl.ini - Qwen3.6 27B Q3_K_XL no-MTP presets at 204800 and 262144 q8 KV.
- examples/llamacpp-single-5060ti-qwen36-27b-iq4xs.ini - Qwen3.6 27B IQ4_XS no-MTP preset at 32768 q8 KV.
- examples/llamacpp-single-5060ti-qwen36-35b-a3b-iq3xxs.ini - Qwen3.6 35B A3B IQ3_XXS thinking presets at 204800 and native max context.

Qwen3.6 27B MTP Q4_XL is not currently a valid one-card GPU-only preset on this seed system because the model allocation fails on a single 16GB card. The current useful one-card MTP/no-MTP comparison is Qwen3.5 9B. For high-context 27B on one card, the current clean route is Q3_K_XL with q8 KV rather than lowering the KV cache precision on the larger IQ4_XS file.

## Current Comparison Gaps

- Qwen3.6 27B no-MTP on 2x5060ti with the same quant/context as the MTP route, if a clean non-MTP route is available.
- BeeLlama DFlash still needs careful framing. The first clean 27B result is single-card Q3_K_XL at 8K; the local dual-card branch fixes the sequence-position failure but does not yet give a broad speedup. The new 35B-A3B DFlash row is strongest on code-generate and weaker on long-retrieval.
- Qwen3.6 35B A3B NVFP4/MTP belongs in a separate vLLM engine lane, not mixed into the llama.cpp GGUF rows.
- Reasoning-budget sweeps for Qwen3.6 35B A3B should be added as quality/latency rows once the baseline speed data is stable.
- Community multi-card submissions should start with the same prompt sets and schema fields so 3x/4x results can sit beside the 1x and 2x lanes.

## Benchmark Hygiene

When adding results, say whether tokens/sec is decode-only or end-to-end, include generated token count, prompt/context size, runtime version, quant, KV cache dtype, MTP/speculative settings, thinking mode, and reasoning budget.
