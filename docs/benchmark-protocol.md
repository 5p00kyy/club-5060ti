# Benchmark Protocol

This protocol is for results that should be compared across recipes, engines, and community machines. Exploratory notes are still useful, but they should not be promoted into comparison tables until the setup details below are present.

## Scope

Canonical data should focus on currently useful RTX 5060 Ti recipes and clearly mark older or incomplete imports as historical. A result can be retained for provenance without being promoted into headline tables.

Primary hardware lanes:

- 1x RTX 5060 Ti 16GB;
- 2x RTX 5060 Ti 16GB;
- 3x/4x+ RTX 5060 Ti 16GB community multi-card setups;
- mixed RTX 5060 Ti plus other CUDA GPUs;
- other CUDA GPUs only when clearly labeled as comparison/adaptation data.

See docs/hardware-lanes.md before comparing across GPU counts.

Primary engine lanes:

- upstream llama.cpp;
- ik_llama.cpp;
- BeeLlama;
- vLLM.

## Required Fields

Every comparable result must include:

- result id and timestamp;
- contributor or source label;
- hardware: GPU count, exact GPU model, VRAM per GPU, driver, CPU, host RAM, inference/container RAM, PCIe layout;
- runtime: engine, engine version or commit, build flags when relevant;
- model: model id, family, parameter class, quant, file/source;
- serving shape: CLI/server, endpoint, tensor parallel or split mode, GPU layers/offload, batch size, ubatch size;
- context: configured context, actual prompt tokens, generated tokens, KV cache type for K and V;
- speculation: MTP, DFlash, ngram, disabled, draft depth, acceptance rate if available;
- benchmark task: prompt set, stream mode, run count, warmup count;
- metrics: prompt tok/s, decode tok/s, wall seconds, TTFT if available, VRAM used per GPU if available;
- caveats: OOMs, Unified Memory, CPU offload, known quality risks, short generation length, non-equivalent settings.

## Canonical Prompt Sets

The site should distinguish benchmark task shapes instead of hiding them behind one speed number.

| Prompt set | Purpose | Default output |
| --- | --- | --- |
| short-chat | Fast sanity generation and simple decode speed | 256 tokens |
| code-generate | Coding-shaped low-entropy output, useful for MTP/DFlash | 768 tokens |
| agent-tool | Agent-style context with tool results and instructions | 512 tokens |
| long-retrieval | Long-context fit and retrieval behavior | 32-128 tokens |
| vision-smoke | Optional multimodal route check | 128 tokens |

Do not compare results from different prompt sets as if they are one benchmark.

For thinking/reasoning models, the request token cap must include both reasoning tokens and final answer tokens. The default output values above describe the target final-answer shape; benchmark runners should add the configured reasoning budget on top when thinking is enabled.

## Presets Before Rows

A benchmark row is not automatically a community recommendation. New work should begin with an exact, copyable preset and use `docs/preset-evidence-workflow.md` to keep raw receipts separate from reviewed public evidence. This protocol remains the common measurement language for seed and community lanes, including 3x/4x+ and mixed-GPU setups.

## Context Tiers

Use these configured context tiers when practical:

| Tier | Tokens | Notes |
| --- | ---: | --- |
| 8K | 8192 | baseline speed and compatibility |
| 32K | 32768 | common real working context |
| 65K | 65536 | long project/chat context |
| 131K | 131072 | high-context stress |
| 204K | 204800 | dual-16GB upper lane for selected models |
| native-max | model metadata max | only when a model-specific recipe supports it |

For long-retrieval tests, record both configured context and actual prompt tokens. A 204K configured context with a 7K prompt is not a 204K long-context result.

## Comparison Rules

Use strict comparison tables only when these are equivalent:

- same target model family and quant class, or a table explicitly marked as recipe comparison;
- same configured context tier;
- same actual prompt set;
- same generated-token budget;
- same KV cache type or clearly separated rows;
- same engine lane or a table explicitly marked cross-engine;
- same thinking/reasoning mode and reasoning budget.

Recipe tables may mix settings, but they must be labeled as recipe tables rather than engine benchmarks.

For MTP and other speculative decoding work, keep baseline and accelerated lanes separate. A useful matrix records both a no-MTP baseline and the MTP/speculative variant for the same model, quant, prompt set, context tier, KV cache, thinking mode, and reasoning budget whenever the engine supports both.

## Benchmark Gap Matrix

Prioritize missing benchmark rows that are most useful for current 16GB and dual-16GB setups:

| Priority | Model | Engine lanes | Why |
| --- | --- | --- | --- |
| P0 | Qwen3.6 27B MTP | llama.cpp, ik_llama.cpp, BeeLlama, vLLM where viable | main dense 27B target for dual 16GB |
| P0 | Qwen3.5 9B MTP | llama.cpp | practical small long-context baseline |
| P1 | Qwen3.6 35B A3B | llama.cpp, vLLM where viable | strong MoE/active-params comparison |
| P1 | Gemma 4 26B/31B | llama.cpp/vLLM where supported by the runtime | useful non-Qwen comparison |
| P2 | non-default Qwen3.6 27B variants | llama.cpp/vLLM | model-variant comparison, not default headline |

## Result Promotion Levels

| Level | Meaning |
| --- | --- |
| exploratory | local experiment, useful but incomplete |
| recipe | reproducible launch and basic smoke passed |
| benchmark | schema-complete speed result with protocol fields |
| verified | repeated run or community reproduction on comparable hardware |
| deprecated | retained for history but hidden from headline views |

The site should default to recipe, benchmark, and verified results. Exploratory and deprecated data should be visible only when a user enables it.
