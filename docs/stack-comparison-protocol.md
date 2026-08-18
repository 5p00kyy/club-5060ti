# Qwen3.8 stack comparison protocol

This protocol compares complete retained serving stacks. It does not isolate weight quantization because the engine, weight format, KV precision, speculative decoding, and serving implementation also differ.

## Compared stacks

- vLLM: Qwen3.8 27B NVFP4, FP8 KV, tensor parallel 2, MTP3, one active sequence.
- llama.cpp: Qwen3.8 27B Q6_K, f16 KV, tensor split 50,50, draft-MTP, one active sequence.

Record the exact runtime build, launch profile, clocks, driver, context allocation, batch settings, and speculation settings with every run. A comparison against a newer runtime is new evidence and must not be merged into an older receipt.

## Fairness boundary

- Use the same dual RTX 5060 Ti 16GB cards and the same locked SM clock.
- Keep one stack loaded at a time and run requests sequentially.
- Use identical user prompts, output budgets, thinking mode, temperature, and seed where both engines support them.
- Use actual server-reported prompt and completion token counts. Do not assume nominal filler size equals tokenized context.
- Match prompts up to the lower retained ceiling. Report any higher Q6-only context result separately.
- Prefix every long-context request with a fresh nonce and disable prompt-cache reuse.
- Separate controlled non-thinking throughput from thinking-enabled quality and end-to-end latency.
- Report this as a stack comparison, not an NVFP4-versus-Q6 quality attribution.

## Speed matrix

Run one warmup followed by at least three measured requests for:

- short chat;
- code generation;
- real function calling;
- sustained 1,024-token generation;
- long-context retrieval near 8K, 32K, 64K, 96K, and 115K actual prompt tokens;
- sustained 1,024-token generation near 8K, 64K, and 115K prompt tokens.

Capture wall time, actual tokens, client TTFT, server TTFT, server prefill time, server decode time, decode rate, prefill rate, VRAM, clocks, and failures. For vLLM, Prometheus deltas are valid only on an otherwise idle single-model endpoint. For llama.cpp, retain its response `timings` object.

## Quality matrix

Run the V2 `scripts/run_stack_quality.py` suite unchanged against each stack. The 68-record suite covers:

- arithmetic, mathematics, logic, code reasoning, and knowledge cases with thinking enabled;
- instruction following, strict JSON and schema extraction, factual checks, privacy handling, and an actual function-call contract;
- dedicated thinking-enabled exact-answer problems over seeds `2234` and `2235`;
- calibrated early, middle, and late marker retrieval near 8K, 32K, 64K, 96K, and 115K actual prompt tokens.

Use the same thinking-enabled policy and `max_tokens=8192` cap on both stacks. Record `answer_correct` and `completion_contract` separately; `combined_exact_contract_pass` requires both. Public evidence must use the V2 semantics and must not publish raw responses or hidden reasoning.

Keep complete raw responses local. Public evidence should contain deterministic grades, compact excerpts where needed, and explicit caveats, never private endpoints, credentials, absolute paths, or hidden reasoning traces.

## Interpretation

Prefer category-level pass counts and repeated-run consistency over one aggregate score. A speed advantage does not establish quality equivalence. A deterministic pass does not establish general model quality. Any qualitative review must be blinded to stack identity and reported separately from objective grades.
