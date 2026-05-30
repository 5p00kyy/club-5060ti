# llama.cpp: Qwen3.5 9B MTP GGUF

This is a small-model GGUF check on the same 2x RTX 5060 Ti 16GB seed machine.

The useful public recipe is the model's native max context using the stock GGUF metadata.

## Model

- Repository: `unsloth/Qwen3.5-9B-MTP-GGUF`
- Tested file: `Qwen3.5-9B-UD-Q4_K_XL.gguf`
- Runtime: seed results used llama.cpp MTP build `9032-5d5f1b46e`; current upstream examples should use a post-merge build such as `9190 (b64739ea3)`.

## Native Max-Context Preset

~~~ini
[Qwen3.5-9B-MTP-Q4-native-max]
model = /path/to/Qwen3.5-9B-UD-Q4_K_XL.gguf
ctx-size = 262144
cache-type-k = q8_0
cache-type-v = q8_0
n-gpu-layers = 99
tensor-split = 1,1
batch-size = 4096
ubatch-size = 1024
flash-attn = on
spec-type = draft-mtp
spec-draft-p-min = 0.75
spec-draft-n-max = 2
jinja = on
parallel = 1
~~~

See examples/llamacpp-qwen35-9b-mtp-native-max.ini.

For one RTX 5060 Ti 16GB, use examples/llamacpp-single-5060ti.ini. The single-card version removes `tensor-split`, keeps q8 KV, and uses batch 1024 / ubatch 256.

## Direct Server Shape

~~~bash
llama serve \
  --host 127.0.0.1 \
  --port 18080 \
  --model /path/to/Qwen3.5-9B-UD-Q4_K_XL.gguf \
  --alias Qwen3.5-9B-MTP-Q4-q8kv-262144 \
  --ctx-size 262144 \
  --cache-type-k q8_0 \
  --cache-type-v q8_0 \
  --n-gpu-layers 99 \
  --tensor-split 1,1 \
  --flash-attn on \
  --parallel 1 \
  --batch-size 4096 \
  --ubatch-size 1024 \
  --jinja \
  --reasoning-format auto \
  --no-mmap \
  --no-warmup \
  --spec-type draft-mtp \
  --spec-draft-p-min 0.75 \
  --spec-draft-n-max 2
~~~

## MTP Flag Compatibility

The older seed build `9032-5d5f1b46e` accepted `--spec-type mtp`. Merged upstream llama.cpp now uses `--spec-type draft-mtp` with `--spec-draft-p-min 0.75`. Keep reported results tied to the exact build and speculative flags.

## Observed Result

At native `ctx-size 262144` with q8 KV and MTP draft 2 on 2x RTX 5060 Ti 16GB:

- the server loaded and answered at the full native context setting
- warmed 512-token decode: 72.50 tok/s
- prompt eval: 26 prompt tokens at 356.79 tok/s
- MTP draft acceptance: 260/502, about 51.8%

At native `ctx-size 262144` with q8 KV and MTP draft 2 on 1x RTX 5060 Ti 16GB:

- the server loaded and answered at the full native context setting
- loaded VRAM after startup: about 11535 MiB
- 251-token short decode: 85.23 tok/s
- 126053-token needle retrieval passed, recovering `COBALT-9137`
- long-prompt eval: 1006 tok/s over 126053 prompt tokens
- long-prompt decode: 53.36 tok/s over 10 generated tokens
- VRAM during the long prompt: about 13091 MiB

## Caveats

- This is a fit and speed receipt, not a general quality claim.
- Do not assume draft/speculative decoding is active just because the flags are present. Check logs for `speculative decoding context initialized` and draft acceptance.
- Larger context extrapolation is not the recommended public recipe for this model. Keep the simple native max-context config unless you are deliberately doing stress tests.
