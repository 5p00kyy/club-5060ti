# Qwen3.6 35B A3B Checks

The 35B A3B model is included as an additional 5060 Ti reference point.
Single-card IQ3_XXS long-context results live in docs/single-5060ti.md; this page keeps the larger-quant and dual-card checks together.

## llama.cpp GGUF

Small-context text smoke test:

| Field | Value |
| --- | --- |
| Runtime | llama.cpp MTP build 9032-5d5f1b46e |
| Model | unsloth/Qwen3.6-35B-A3B-GGUF |
| File | Qwen3.6-35B-A3B-UD-IQ4_XS.gguf |
| Context | 8192 |
| KV cache | q8_0 / q8_0 |
| GPU split | 1,1 |
| Result | 90.45 tok/s over 256 generated tokens |

See examples/llamacpp-qwen36-35b-a3b.ini for the sanitized preset.

## BeeLlama DFlash

BeeLlama DFlash has an exploratory single-card 35B-A3B result using the
`UD-IQ3_XXS` target with q8 KV and a matching 35B-A3B DFlash drafter.

The useful row is workload-specific: at 204800 configured context, DFlash
`n16/x512` improved code-generate from 89.20 tok/s to 138.26 tok/s on one
RTX 5060 Ti, while short-chat and agent-tool improved only modestly. A
27061-token long-retrieval prompt fit at a lower context but was slower with
DFlash than no-spec because acceptance was low.

See docs/beellama-dflash.md and
data/results/seed-beellama-qwen36-35b-a3b-dflash-20260523.json.

## vLLM NVFP4/MTP

The vLLM path uses RedHatAI/Qwen3.6-35B-A3B-NVFP4 with tensor parallel across both cards, fp8 KV cache, FlashInfer MoE, and MTP speculative decoding.

The public example uses 32768 context as a conservative starting point. Larger-context startup checks need fresh speed rows before they belong in the benchmark table.

Observed startup checks include 32768 and 131072 context reaching the OpenAI-compatible model list endpoint. The current benchmark table only includes this as a fit/startup receipt, not a speed claim.

See examples/vllm-qwen36-35b-a3b-nvfp4.sh for the sanitized launch command.
