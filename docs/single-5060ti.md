# Single RTX 5060 Ti 16GB Starter Notes

The main seed results in this repo use 2x RTX 5060 Ti 16GB. A single 5060 Ti can still be useful, but it is a different target: less total VRAM, no tensor split, and less room for large dense models or higher-quality quants.

Treat this page as a conservative starting point for community testing. The rows below are seed-machine receipts, not universal 16GB guarantees.

## Best Starting Path

Start with llama.cpp and GGUF models.

For one 16GB card, smaller GGUF models and lower quants are the practical first target. The Qwen3.5 9B MTP Q4 GGUF is a safe starter and has both MTP and no-MTP single-card presets. For Qwen3.6 27B, the current high-context route is Q3_K_XL with q8 KV; IQ4_XS is useful when you want a stronger quant at lower context. For Qwen3.6 35B A3B, use the lower single-card MoE quant below rather than copying the dual-card Q4/Q6 recipes.

Example preset:

~~~ini
[Qwen3.5-9B-MTP-Q4-single-5060ti]
model = /path/to/Qwen3.5-9B-UD-Q4_K_XL.gguf
ctx-size = 262144
cache-type-k = q8_0
cache-type-v = q8_0
n-gpu-layers = 99
batch-size = 1024
ubatch-size = 256
flash-attn = on
spec-type = draft-mtp
spec-draft-p-min = 0.75
spec-draft-n-max = 2
jinja = on
parallel = 1
reasoning = off
chat-template-kwargs = {"enable_thinking": false}
~~~

See examples/llamacpp-single-5060ti.ini for both the MTP and no-MTP 9B presets.

If you want more headroom for other services, start lower and raise context in steps. Do not jump straight to the largest context unless you are deliberately stress testing.

## Qwen3.5 9B Single-Card Recipe

This is the tested small-model llama.cpp recipe on one RTX 5060 Ti 16GB, with no unified-memory overcommit and one GPU visible. The same Qwen3.5 9B MTP GGUF can be run with MTP enabled or with speculation disabled for a clean baseline.

Tested with batch 1024, ubatch 256:

| Model | Quant | Context | GPU layers | Result |
| --- | --- | --- | --- | --- |
| Qwen3.5 9B | Q4_K_XL | 262144 | full | no MTP, protocol run: 63 tok/s short/code/agent decode, 57-58 tok/s long-retrieval short-answer decode |
| Qwen3.5 9B MTP | Q4_K_XL | 262144 | full | draft-MTP n=2, protocol run: 82 tok/s short-chat, 96 tok/s code-generate, 77 tok/s agent/long-retrieval short-answer decode |
| Qwen3.5 9B MTP | Q4_K_XL | 262144 | full | q8 KV, 126053-token needle retrieval OK, 1006 tok/s prompt eval, 53.36 tok/s decode, about 13091 MiB VRAM during the long prompt |
| Qwen3.5 9B MTP | Q4_K_XL | 262144 | full | q8 KV, 251-token short decode, 85.23 tok/s decode, about 11535 MiB VRAM loaded |

Recommended example:

- examples/llamacpp-single-5060ti.ini

## Qwen3.6 Single-Card Recipes

These are the tested single-card llama.cpp GGUF recipes on one RTX 5060 Ti 16GB, with no unified-memory overcommit and one GPU visible.

Tested with batch 512, ubatch 128:

| Model | Quant | Context | GPU layers | Result |
| --- | --- | --- | --- | --- |
| Qwen3.6 27B | Q3_K_XL | 262144 | full | q8 KV, fit check passed, tiny completion OK, 12379 MiB VRAM loaded |
| Qwen3.6 27B | Q3_K_XL | 204800 | full | q8 KV, protocol run: 22.76 tok/s short-chat, 22.68 tok/s code-generate, 22.67 tok/s agent-tool, 20.70 tok/s long-retrieval short-answer decode |
| Qwen3.6 27B | IQ4_XS | 32768 | 65/65 | q8 KV, 64-token completion OK, 24.65 tok/s decode, 15561 MiB VRAM loaded |
| Qwen3.6 27B | IQ4_XS | 16384 | 65/65 | q8 KV, 64-token completion OK, 24.65 tok/s decode, 15021 MiB VRAM loaded |
| Qwen3.6 35B A3B | IQ3_XXS | 262144 | 41/41 | q8 KV, 93636-token needle retrieval OK, 938 tok/s prompt eval, 46.48 tok/s decode, 15345 MiB VRAM loaded |
| Qwen3.6 35B A3B | IQ3_XXS | 204800 | 41/41 | q8 KV, 64-token completion OK, 92.83 tok/s decode, 14709 MiB VRAM loaded |
| Qwen3.6 35B A3B | IQ3_XXS | 131072 | 41/41 | q8 KV, 64-token completion OK, 93.04 tok/s decode, 13905 MiB VRAM loaded |
| Qwen3.6 35B A3B | IQ3_XXS | 32768 | 41/41 | q8 KV, 64-token completion OK, 89.06 tok/s decode, 12885 MiB VRAM loaded |
| Qwen3.6 35B A3B | IQ3_XXS | 16384 | 41/41 | q8 KV, 64-token completion OK, 91.72 tok/s decode, 12717 MiB VRAM loaded |

Recommended examples:

- examples/llamacpp-single-5060ti-qwen36-27b-q3kxl.ini
- examples/llamacpp-single-5060ti-qwen36-27b-iq4xs.ini
- examples/llamacpp-single-5060ti-qwen36-35b-a3b-iq3xxs.ini

## Qwen3.8 Single-Card Recipes

Tested on one RTX 5060 Ti 16GB with build `10431 (1692f9e50)`, batch 512, ubatch 128, MTP n=2 p-min=0.1. Qwen3.8 emits substantial hidden reasoning; the published evidence used the thinking-enabled route and required a client-visible final answer.

| Model | Quant | KV | Context | Result |
| --- | --- | --- | --- | --- |
| Qwen3.8 27B | IQ3_XXS | q8 | 65536 | recommended: 2x ~57.7K-token retrieval checks passed, 2x ~45.9K-token sustained visible-answer generations passed; ~562 tok/s prefill, ~29.8 tok/s decode, peak VRAM ~14.8GB |
| Qwen3.8 27B | IQ3_XXS | f16 | 32768 | experimental: 2x ~28.9K-token retrieval checks passed (~14.3GB), but both sustained runs exhausted the 1536-token output budget in hidden reasoning without a client-visible answer |

Recommended example: examples/llamacpp-qwen38-27b-single-5060ti.ini (the f16 32K variant is the second section in the same file). See docs/llamacpp-qwen38.md for the full Qwen3.8 routes and evidence.

## Larger-Quant Fallbacks

Higher-quality/larger GGUF quants need partial CPU offload or fail on a single 16GB card.

GPU-only checks failed:

- Qwen3.6 27B IQ4_XS q8 KV failed at 65536 context allocating the KV cache. Switching to q4 KV made 65536 context fit on the seed card, but the project avoids treating q4 KV as the normal path when a lower model quant can keep q8 KV.
- Qwen3.6 27B IQ4_XS q4 KV still failed at 98304 and 110080 context allocating the KV cache on the seed card.
- Qwen3.6 27B Q4_K_M at 4096 context failed allocating compute buffers after loading about 15.3 GiB of model data on GPU.
- Qwen3.6 27B MTP Q4_XL failed model allocation on one 16GB card.
- Qwen3.6 35B A3B IQ4_XS failed model allocation on one 16GB card.

That means the current useful single-card MTP/no-MTP comparison is Qwen3.5 9B. Qwen3.6 27B has a single-card no-MTP baseline, but not a GPU-only MTP baseline with the current Q4_K_XL MTP file.

Partial-offload fallbacks that completed:

| Model | Quant | Context | GPU layers | Result |
| --- | --- | --- | --- | --- |
| Qwen3.6 27B | Q4_K_M | 4096 | 60/65 | 64-token completion OK, 12.36 tok/s decode, about 14.7 GiB VRAM loaded |
| Qwen3.6 27B | Q4_K_M | 4096 | 56/65 | 64-token completion OK, 9.33 tok/s decode, about 13.8 GiB VRAM loaded |
| Qwen3.6 35B A3B | IQ4_XS | 4096 | 32/41 | 64-token completion OK, 17.08 tok/s decode, about 13.2 GiB VRAM loaded |

Example partial-offload presets:

- examples/llamacpp-single-5060ti-qwen36-27b-q4km.ini
- examples/llamacpp-single-5060ti-qwen36-35b-a3b.ini

## Launch Shape

Pin the server to one GPU so the result is clearly single-card:

~~~bash
CUDA_VISIBLE_DEVICES=0 llama serve \
  --model /path/to/Qwen3.5-9B-UD-Q4_K_XL.gguf \
  --ctx-size 262144 \
  --cache-type-k q8_0 \
  --cache-type-v q8_0 \
  --n-gpu-layers 99 \
  --flash-attn on \
  --parallel 1 \
  --batch-size 1024 \
  --ubatch-size 256 \
  --jinja \
  --spec-type draft-mtp \
  --spec-draft-p-min 0.75 \
  --spec-draft-n-max 2
~~~

For ordinary single-card use, start below the model's native maximum context and raise context only after short prompts are stable. Qwen3.5 9B MTP Q4 is the least constrained observed single-card starter because native 262144 context works with q8 KV. Qwen3.6 35B A3B IQ3_XXS is the strongest observed long-context larger-model fit in the current seed data, including a native-262144 slot and a 93636-token needle retrieval pass. For dense Qwen3.6 27B on one 16GB card, use Q3_K_XL when high context matters and IQ4_XS when a stronger quant matters more than context; q4 KV is only a fallback tradeoff, not the normal recommendation.

## What To Report

Useful single-card reports should include:

- exact GPU model and VRAM
- driver and CUDA version
- llama.cpp commit or build source
- model file and quant
- context length
- KV cache type
- batch and ubatch sizes
- prompt eval tok/s and decode tok/s
- peak VRAM during startup and during a real prompt
- whether MTP/speculative decoding was active, including draft acceptance if available

## Expectations

- 27B-class recipes from the dual-card setup should not be copied directly onto one 16GB card.
- Smaller GGUF models, lower quants, lower context, and q8 KV are the sane first pass. Use lower KV precision only when context fit requires it.
- For 27B/35B on one card, use lower quants first. Partial CPU offload is a fallback for larger quants, not the best starting recipe.
- If startup fits but long prompts fail, reduce context first, then batch/ubatch.
- vLLM can still be tested on one card, but the current repo evidence is strongest for dual-card vLLM serving.
