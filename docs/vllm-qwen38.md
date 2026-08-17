# vLLM: Qwen3.8 27B NVFP4/MTP on 2x RTX 5060 Ti

This is the current recommended vLLM lane for two RTX 5060 Ti 16GB cards. The older [Qwen3.6 notes](vllm-qwen36.md) remain historical.

## Retained profile

Use [`examples/vllm-qwen38-27b-nvfp4.sh`](../examples/vllm-qwen38-27b-nvfp4.sh).

- model: `unsloth/Qwen3.8-27B-NVFP4`
- vLLM: `0.27.2rc1.dev110+gacb0f1dcd`
- tensor parallel: 2
- context: 122,880
- FP8 KV with an explicit 2,500,000,000-byte allocation per GPU
- MTP speculative tokens: 3
- maximum batched tokens: 2,048
- maximum sequences: 1
- CUDA graph capture size: 4
- prefix caching: off
- Qwen3 reasoning and `qwen3_coder` tool parsing enabled

## Verified result

Three consecutive streamed runs used 118,660 prompt tokens and generated 512 tokens.

| Metric | Median | Range |
| --- | ---: | ---: |
| Prefill | **952.50 tok/s** | 952.18–953.01 |
| Decode | **67.29 tok/s** | 66.99–67.41 |
| Time to first token | **124.58 s** | 124.51–124.62 |
| Wall time | **132.16 s** | 132.14–132.21 |

Both cards used about 15,613 MiB under the completed workload. Reported KV capacity was exactly 122,880 tokens, so full-context concurrency is 1.00x. This is a single-sequence profile, not a throughput-serving profile.

The bounded quality gates passed:

- OpenAI tool call emitted the exact requested function and JSON arguments.
- A 49,125-token archive recovered three markers placed near 8%, 50%, and 92%.
- The health endpoint remained HTTP 200.

## Why 122,880 and 2,048

The original 131,072/512 MTP3 baseline reached about 886.62 tok/s prefill and 64.87 tok/s decode. The retained profile improves prefill by about 7.4% and decode by about 3.7%, while preserving a practical 120K-class context.

Larger chunks were not production-safe:

- 4,096 could start only after changing graph-memory accounting and pinning KV, but repeatedly OOMed on the first real 118K prefill.
- 1,600 reached 921.62 tok/s prefill.
- 1,024 repeated at 912.50 tok/s median prefill.

The requested 1,000+ prefill and 60+ decode target was not reached. Publishing 952.50 as the measured ceiling is more useful than retaining an unstable 4,096 profile.

## Compile cache and KV sizing

Persist `/root/.cache/vllm` into the container. It reduced cached compilation from 177.67 seconds to 1.95 seconds and reload-to-health from 443.42 seconds to 131.88 seconds.

Do not combine that mount with automatic KV sizing on this build. Cached startup produced a much cheaper profiling pass and vLLM then allocated 182,248 KV tokens, which does not preserve realistic activation headroom. Pinning `--kv-cache-memory 2500000000` restored exactly 122,880 KV tokens and survived repeated full-load runs.

## Quality and comparison limits

NVFP4 weights with FP8 KV are not quality-equivalent to the separate llama.cpp Q6_K/f16-KV preset. Compare each lane on its own tested purpose:

- vLLM: much faster prefill, MTP3 decode, OpenAI-compatible tool serving
- llama.cpp: GGUF portability and the separately verified Q6_K/f16-KV route

Evidence:

- `data/results/seed-qwen38-27b-nvfp4-vllm-2x5060ti-20260817.json`
- `data/quality/seed-qwen38-27b-nvfp4-vllm-2x5060ti-quality-20260817.json`
