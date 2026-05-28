---
name: Result report
about: Share an RTX 5060 Ti local LLM result
title: "[result] "
labels: result
---

## Privacy Checklist

- [ ] I removed private IPs, hostnames, tokens, and personal paths.
- [ ] I validated JSON with `python3 scripts/validate_results.py PATH_TO_RESULT_JSON` when available.
- [ ] I attached or linked the result JSON when available.
- [ ] This may be a raw report; maintainers can normalize missing fields.

## Raw or Structured Submission

- [ ] Raw issue report (maintainers can normalize)
- [ ] Structured JSON report attached/linked

## Hardware

- Hardware lane: 
- GPU count:
- GPU model:
- VRAM per GPU:
- Driver:
- CPU:
- Host RAM:
- Inference/container RAM:
- Motherboard/system:
- PCIe layout/link width:
- OS/container:

## Runtime

- Runtime/engine:
- Runtime version/commit:
- Build flags (if known):
- Model:
- Quant:
- Source:
- Route (server/cli/container):
- Launch command/config:

## Settings

- Context configured:
- Actual prompt tokens (if known):
- KV cache dtype (K/V):
- Tensor parallel:
- Tensor split / split mode:
- Launch split settings (`tensor_split`, `split_mode`, etc.):
- MTP/speculative settings:
- Thinking/reasoning enabled:
- Batch size / ubatch size:

## Result

- Prompt tokens:
- Generated tokens:
- Was speed measured as:
  - [ ] prompt eval / prefill tok/s
  - [ ] decode tok/s
  - [ ] end-to-end tok/s
- Prompt eval tok/s:
- Decode tok/s:
- End-to-end tok/s:
- Prompt sets:
- Runs / warmups:
- TTFT/latency (if available):
- Notes/warnings:
- Verified (`yes/no`):

## Optional Report Output

You can generate a starter report with:

~~~bash
python3 scripts/run_openai_bench.py \
  --base-url http://127.0.0.1:8000/v1 \
  --model your-model-name \
  --prompt-set short-chat \
  --prompt-set code-generate \
  --prompt-set agent-tool \
  --runs 1 \
  --no-thinking \
  --output data/results/community-your-run.json \
  --report-output my-result.md
bash scripts/report.sh --url http://127.0.0.1:8000 --model your-model-name >> my-result.md
~~~
