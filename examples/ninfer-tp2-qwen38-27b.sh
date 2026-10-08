#!/usr/bin/env bash
set -euo pipefail

# NInfer TP2 serving Qwen3.8-27B QUASAR NVFP4 on 2x RTX 5060 Ti 16GB.
# Build ValerioDolci/ninfer-tp2 (tested at be178778) with `cmake --preset release`.
# Artifact: Feyd89/Qwen3.8-27B-QUASAR-QAT-nvfp4-NInfer (qwen3_8_27b_quasar_nvfp4.ninfer).
# See docs/ninfer-tp2-qwen38.md for the measurements behind these choices.

NINFER_SERVE="${NINFER_SERVE:-./build/apps/ninfer-serve}"
MODEL="${MODEL:-$HOME/models/qwen3_8_27b_quasar_nvfp4.ninfer}"
PORT="${PORT:-8092}"
API_KEY="${API_KEY:?set API_KEY}"
CTX="${CTX:-196608}"              # verified with vision and 8 state slots
THINK_CAP="${THINK_CAP:-16384}"   # default thinking budget; stops runaway reasoning

exec "$NINFER_SERVE" "$MODEL" \
  --host 0.0.0.0 --port "$PORT" --api-key "$API_KEY" \
  --model-id qwen3.8-27b-nvfp4 \
  --tp 2 --devices 0,1 \
  --kv-dtype int8 \
  --max-context "$CTX" --kv-capacity "$CTX" \
  --max-concurrency 2 --device-state-slots 8 \
  --spec mtp --draft-tokens 3 \
  --vision --vision-device 0 --max-vision-tokens 4096 \
  --default-thinking-budget "$THINK_CAP"
