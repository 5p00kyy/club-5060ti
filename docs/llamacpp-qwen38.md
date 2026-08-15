# llama.cpp: Qwen3.8 27B GGUF

Qwen3.8 27B with built-in multi-token prediction (MTP) from `unsloth/Qwen3.8-27B-GGUF`. This page covers the measured seed routes for RTX 5060 Ti systems. Preset and evidence bundles are the canonical reference; the INIs below are copyable starting points.

## Required Build

The seed evidence used upstream llama.cpp build `10431 (1692f9e50)` with MTP flags `--spec-type draft-mtp`, `--spec-draft-p-min 0.1`, `--spec-draft-n-max 2`. Benchmark rows are tied to the exact runtime; do not mix flag spellings or build versions without recording them.

## Recommended Route: Single Card 64K q8 KV

Preset: `qwen38-27b-iq3xxs-1x5060ti` (recommended). Evidence: `data/evidence/qwen38-27b-iq3xxs-1x5060ti-64k.json` (published).

~~~ini
[Qwen3.8-27B-IQ3_XXS-single-5060ti]
model = /path/to/Qwen3.8-27B-UD-IQ3_XXS.gguf
ctx-size = 65536
n-gpu-layers = 99
cache-type-k = q8_0
cache-type-v = q8_0
temp = 1.0
top-k = 20
top-p = 0.95
min-p = 0
presence-penalty = 0.0
repeat-penalty = 1.0
batch-size = 512
ubatch-size = 128
jinja = on
parallel = 1
spec-type = draft-mtp
spec-draft-p-min = 0.1
spec-draft-n-max = 2
reasoning = on
~~~

On a two-card host, point the single-card route at one visible card, for example `CUDA_VISIBLE_DEVICES=0` in the launch environment. One request slot, one GPU. This is not a concurrency recommendation.

Measured on the seed single-card lane with q8 KV at 64K (peak VRAM ~14.8GB):

- Two uncached retrieval checks passed at ~57.7K prompt tokens (~562 tok/s prefill).
- Two sustained visible-answer generations passed at ~45.9K prompt tokens (~29.8 tok/s decode, MTP acceptance 0.627).
- The model emits substantial hidden reasoning; the profile required a client-visible final answer.

64K is the highest useful tier validated on this route. On this exact one-card setup, 64K and 96K f16 KV failed to allocate, and 96K q8 failed while creating the MTP context. This is not a maximum-context claim.

## Experimental Route: Single Card 32K f16 KV

Preset: `qwen38-27b-iq3xxs-f16-32k-1x5060ti` (experimental). Evidence: `data/evidence/qwen38-27b-iq3xxs-f16-32k-1x5060ti-32k.json` (candidate).

Use the same INI with `ctx-size = 32768`, `cache-type-k = f16`, `cache-type-v = f16`. The f16 KV route fit in ~14.3GB and passed two retrieval checks at ~28.9K prompt tokens (~646 tok/s prefill, ~42.9 tok/s retrieval decode), but both sustained runs exhausted the 1536-token output budget in hidden reasoning without reaching the required client-visible answer. Capable/experimental, not recommended; the q8 KV 64K route is the published single-card preset.

## Recommended Dual-Card Route: 131K Q6_K

Preset: `qwen38-27b-q6-2x5060ti` (recommended). Evidence: `data/evidence/qwen38-27b-q6-2x5060ti-131k.json` (published).

~~~ini
[Qwen3.8-27B-Q6-dual-5060ti]
model = /path/to/Qwen3.8-27B-Q6_K.gguf
ctx-size = 131072
n-gpu-layers = 99
cache-type-k = f16
cache-type-v = f16
split-mode = tensor
tensor-split = 50,50
temp = 1.0
top-k = 20
top-p = 0.95
min-p = 0
presence-penalty = 0.0
repeat-penalty = 1.0
batch-size = 2048
ubatch-size = 512
jinja = on
parallel = 1
spec-type = draft-mtp
spec-draft-p-min = 0.1
spec-draft-n-max = 2
reasoning = on
~~~

Measured on the seed dual-card lane with f16 KV and tensor split 50,50 at 131K:

- Two uncached retrieval checks passed at ~115.4K prompt tokens (~598 tok/s prefill).
- Only one of two sustained repeats produced the required client-visible output (~37.8 tok/s decode); the strict gate did not pass.
- 131K is the highest tier tested here, not a maximum-context claim.

## Measurement Caveats

All Qwen3.8 seed runs were text-only (no image projector) and measured with the seed cards' core/SM clock locked at 2300 MHz; throughput figures are specific to that operating point. See docs/hardware.md for the full seed baseline.
