# Community Result Template (Copy/Paste)

Use this template directly in a GitHub issue for fast submissions. Raw issue reports are welcome—include what you know and leave unknown items as `unknown`.

- Submission type: Raw issue report (maintainers can normalize)
- Verification status: `not verified`

## Basic Result Metadata

- Contributor (optional):
- Source/label:
- Submission date:
- Hardware lane: (1x5060ti / 2x5060ti / multi-5060ti / mixed-5060ti-cuda / other-cuda)
- GPU count:
- GPU model:
- VRAM per GPU:
- Driver:
- CPU:
- Host RAM:
- Inference/container RAM:
- PCIe layout/link width:
- Motherboard/system:
- OS/container runtime:

## Runtime & Model

- Runtime/engine:
- Runtime version or commit:
- Build flags (if known):
- Model id:
- Family/variant:
- Source:
- Quant:
- Launch command or config:

## Serving Shape (required)

- Route/server mode (server/cli/container):
- Context configured:
- Actual prompt tokens (if known):
- Generated tokens:
- KV cache dtype (K/V):
- Tensor parallel:
- Tensor split / split mode:
- Launch split settings (e.g., `tensor_split`, `split_mode`):
- MTP/speculative settings:
- Thinking/reasoning: on/off/unknown
- Batch size / ubatch size:
- Prompt set(s):
- Runs / warmups:
- Stream mode:

## Speed / Accuracy Details

- Specify which metric was measured: prefill (prompt eval), decode, and/or end-to-end.
- Prefill tok/s (prompt eval tok/s):
- Decode tok/s:
- End-to-end tok/s:
- TTFT/latency (if available):
- Any notable caveats:

## Example Submission Block

- Submission type: Raw issue report (maintainers can normalize)
- Verification status: not verified

Hardware lane: `2x5060ti`
- GPU count: `2`
- GPU model: `NVIDIA GeForce RTX 5060 Ti`
- VRAM per GPU: `16GB`
- Driver: `unknown`
- Runtime/engine: `llama.cpp`
- Runtime version/commit: `unknown`
- Model id: `Qwen3.6-27B`
- Quant: `Q6`
- Launch command or config: `unknown`
- Context configured: `96K`
- Actual prompt tokens: `unknown`
- Generated tokens: `unknown`
- KV cache dtype (K/V): `f16`
- Tensor parallel: `unknown`
- Tensor split / split mode: `split tensors`
- MTP/speculative settings: `enabled` (`MTP`, depth/acceptance unknown)
- Thinking/reasoning: `unknown`
- Prompt set(s): `short-chat`
- Prefill tok/s (prompt eval tok/s): `unknown`
- Decode tok/s: `~55`
- End-to-end tok/s: `unknown`
- Caveats: `unknown`
