# Qwen3.8 27B matched stack quality comparison — V2 — 2026-08-18

This is a **complete serving-stack comparison**, not proof that NVFP4 and Q6_K have equivalent quality or that any difference is caused by weight quantization alone. The stacks change several variables together: engine, runtime build, weight format, KV-cache precision, and speculative decoding.

The compact public evidence is [`data/quality/seed-qwen38-stack-comparison-quality-20260818.json`](../data/quality/seed-qwen38-stack-comparison-quality-20260818.json). Complete raw responses remain local and are not published.

## Compared stacks

Both stacks served Qwen3.8 27B on the same 2x RTX 5060 Ti 16GB hardware lane, one stack at a time and with one active request slot.

| Stack | Runtime and identity | Weights / KV | Serving identity |
| --- | --- | --- | --- |
| vLLM | vLLM `0.27.2rc1.dev110+gacb0f1dcd` | NVFP4 / FP8 KV | TP2, MTP3, max batched tokens 2,048, max sequences 1, context 122,880 |
| llama.cpp | build `10451`, commit `10bf611e5` | Q6_K / f16 KV | tensor split `50,50`, draft-MTP2, p-min `0.1`, parallel 1, batch 2,048, ubatch 512, context 131,072 |

The comparison uses the retained launch identities, not a generic “vLLM versus llama.cpp” claim. A different runtime, model file, KV type, or speculation setting is new evidence.

## V2 method and policy

The V2 `scripts/run_stack_quality.py` suite ran 68 graded cases per stack:

- 21 base cases, repeated twice; arithmetic, math, logic, code-reasoning, and knowledge cases were thinking-enabled, while instruction, privacy, structured-output, and tool-call cases were contract-focused;
- 8 dedicated thinking-enabled reasoning cases, repeated twice with thinking seeds `2234` and `2235`;
- 5 long-context three-marker retrieval bands (`8K`, `32K`, `64K`, `96K`, `115K`), repeated twice without thinking.

Thinking-enabled cases used the same `max_tokens=8192` cap on both stacks. Temperature was `0` for ordinary cases, thinking temperature `1`, and the base seed was `1234`. Long-context requests used fresh nonces and no prompt-cache reuse. Generated code was never executed. Grading was deterministic: answer correctness and completion-contract shape were recorded separately, and a combined exact-contract pass requires both. There was no LLM judge. Server-reported prompt usage is authoritative for context measurements.

## Exact V2 results

These are three distinct measures over the same 68 records: `answer_correct`, `completion_contract`, and `combined_exact_contract_pass` (both true).

| Stack | Answer correct | Completion contract | Combined exact-contract pass |
| --- | ---: | ---: | ---: |
| vLLM NVFP4 / FP8 KV / MTP3 | **65/68** | **64/68** | **61/68** |
| llama.cpp Q6_K / f16 KV / draft-MTP2 | **66/68** | **68/68** | **66/68** |

The combined column is the strict bounded contract result. It must not be read as a general model-quality score.

## Failure interpretation

- **Shared:** the two `instruction_no_e` records per stack were answer failures. The outputs met the final-line shape, but did not satisfy the instruction that all five words contain no letter `e`.
- **vLLM answer-only:** one `thinking_python` record returned the wrong exact answer (`28` instead of `31`) while still satisfying the FINAL-only completion contract.
- **vLLM formatting-only:** four long-context records (`context_8000`, `context_32000`, and both `context_96000` repeats) had correct marker arrays but were JSON-fenced. Their `answer_correct` grades were true; their completion-contract grades were false.

These diagnostics preserve the distinction between answer correctness and output shape: answer correctness does not imply that the required output contract was met, and a valid output shape does not imply the answer was correct.

## Long-context answer correctness

Both stacks were **10/10 answer-correct** on the long-context marker cases at closely matched actual server-reported prompt-token counts. The vLLM formatting-only fences reduce its strict combined result to 6/10; llama.cpp was 10/10 on both measures.

| Target band | vLLM actual prompt tokens | llama.cpp actual prompt tokens | Answer correctness |
| ---: | ---: | ---: | --- |
| 8,000 | 8,003–8,003 | 8,003–8,005 | 2/2 each |
| 32,000 | 32,012–32,013 | 32,006–32,012 | 2/2 each |
| 64,000 | 64,005–64,007 | 64,003–64,004 | 2/2 each |
| 96,000 | 95,998–96,014 | 95,996–95,998 | 2/2 each |
| 115,000 | 115,007–115,008 | 115,006–115,008 | 2/2 each |

These are marker-retrieval checks, not maximum-context or sustained-throughput claims.

## Reading the result safely

- The thinking-enabled quality policy and the matched 8,192-token cap apply equally to both retained stacks; changing that policy is new evidence.
- The shared harness caps and exact extraction contracts make these useful bounded regression signals, not broad model-quality claims.
- This is a complete-stack comparison: **not quantization-only proof**. It does not isolate NVFP4 versus Q6_K from FP8 versus f16 KV, MTP3 versus draft-MTP2, or either engine implementation.
- Do not publish local raw responses, endpoints, credentials, host details, absolute paths, or hidden reasoning traces; use the compact JSON summary instead.
