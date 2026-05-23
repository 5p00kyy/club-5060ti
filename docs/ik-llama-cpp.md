# ik_llama.cpp First Pass

This page tracks early `ik_llama.cpp` checks for RTX 5060 Ti systems. Do not
treat these rows as promoted benchmark data until the chat-template/thinking
behavior is controlled and rerun under the normal protocol.

Tested build:

- Runtime: `ik_llama.cpp` version `4535`, commit `3f45ba93`.
- Build: CUDA for RTX 5060 Ti / Blackwell.
- Hardware: seed Dell T7810 lane, one RTX 5060 Ti 16GB, driver `595.58.03`.
- Model: `cHunter789/Qwen3.6-27B-i1-IQ4_KS-GGUF`.
- File: `Qwen3.6-27B.i1-IQ4_KS-attn_qkv-IQ4_KSS.gguf`.
- Context: `105216` slot.
- KV: `q4_0/q4_0`.
- Batch: `-b 2048 -ub 512`.
- Launch shape: single GPU visible, full GPU offload, Flash Attention enabled,
  prompt cache disabled.

## Fit Result

The post-style single-card shape fits on one RTX 5060 Ti:

| Item | Observed |
| --- | ---: |
| Model buffer on CUDA0 | 12797 MiB |
| KV buffer on CUDA0 | 1999 MiB |
| Total GPU memory after load | about 15469 MiB |
| Slot context | 105216 tokens |

This is tight but useful: the 14GB KS/KSS file plus q4 KV leaves only a small
amount of free VRAM on a 16GB card.

## Local Speed Probe

The first OpenAI-compatible probe completed, but is not checked into
`data/results` yet because the server still emitted visible `<think>` content
even with reasoning disabled at launch.

| Prompt set | Generated tokens | Decode tok/s | Notes |
| --- | ---: | ---: | --- |
| short-chat | 256 | 26.37 | Visible thinking/template issue still present |
| code-generate | 768 | 26.25 | Visible thinking/template issue still present |
| agent-tool | 512 | 26.16 | Visible thinking/template issue still present |
| long-retrieval | 96 | 20.50 | 27057 prompt tokens; 96-token cap was spent on reasoning, not a clean final answer |

A manual long-retrieval retry with a larger output cap did retrieve
`CLUB-5060TI-NEEDLE-194`, but only after visible reasoning text. That is enough
to show the model can use the long context, not enough for a clean club result.

## Current Interpretation

- The 105k q4-KV one-card fit is real and worth pursuing.
- Throughput is around 26 tok/s on the short/code/tool prompts in this first
  pass, slower than the 35B-A3B MoE rows but in the same broad practical range
  as other dense 27B single-card routes.
- The immediate blocker is not fit; it is getting a clean no-thinking chat
  template or a separate raw-completion retrieval protocol.
- Do not headline this as a quality win from quantization alone. It needs
  controlled retrieval, coding, and tool-prompt checks, not just fit or PPL.

Next useful checks:

- Solve the visible-thinking/template behavior and rerun the normal prompt set.
- Add a raw-completion retrieval check if chat-template suppression remains
  unreliable.
- Test whether a dual-card split improves throughput or only adds headroom.
- Compare against upstream llama.cpp 27B Q3/IQ4 rows with the same prompt sets
  and clear KV-cache settings.
