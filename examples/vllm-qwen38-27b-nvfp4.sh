#!/usr/bin/env bash
set -euo pipefail

# Validated on 2x RTX 5060 Ti 16GB. The explicit KV allocation is important:
# warm compile-cache starts otherwise over-allocate KV from an unrealistically
# cheap profiling pass and can OOM on the first full prefill.

PORT="${PORT:-8000}"
HF_HOME="${HF_HOME:-$HOME/.cache/huggingface}"
VLLM_CACHE="${VLLM_CACHE:-$HOME/.cache/vllm}"
MODEL="${MODEL:-unsloth/Qwen3.8-27B-NVFP4}"
SERVED_MODEL="${SERVED_MODEL:-qwen3.8-27b-nvfp4}"
IMAGE="${IMAGE:-vllm/vllm-openai@sha256:6b084be85c1806afcb69df24d853ebf240b9f0dfca3eaa2252d0096a46a12c58}"

mkdir -p "$HF_HOME" "$VLLM_CACHE"

docker run --rm --init --gpus all --ipc=host --shm-size=16g \
  -p "${PORT}:8000" \
  --ulimit memlock=-1:-1 --ulimit stack=67108864 \
  -v "${HF_HOME}:/root/.cache/huggingface" \
  -v "${VLLM_CACHE}:/root/.cache/vllm" \
  "$IMAGE" "$MODEL" \
  --served-model-name "$SERVED_MODEL" \
  --host 0.0.0.0 --port 8000 \
  --tensor-parallel-size 2 \
  --quantization compressed-tensors \
  --dtype bfloat16 \
  --kv-cache-dtype fp8 \
  --kv-cache-memory 2500000000 \
  --gpu-memory-utilization 0.977 \
  --max-model-len 122880 \
  --max-num-batched-tokens 2048 \
  --max-num-seqs 1 \
  --max-cudagraph-capture-size 4 \
  --speculative-config '{"method":"mtp","num_speculative_tokens":3}' \
  --no-enable-flashinfer-autotune \
  --no-enable-prefix-caching \
  --disable-custom-all-reduce \
  --language-model-only \
  --enable-auto-tool-choice \
  --tool-call-parser qwen3_coder \
  --reasoning-parser qwen3 \
  --generation-config vllm
