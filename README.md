# club-5060ti

Practical local LLM presets, reviewed evidence, and setup notes for RTX 5060 Ti 16GB systems.

The project focus is simple: make RTX 5060 Ti local inference reproducible across one card, two cards, and larger community setups. A **preset** is the thing we recommend someone run. Benchmark receipts prove what that preset can do. Raw experiments remain useful engineering material, but do not become public recommendations merely because a request completed.

The seed system covers 1x and 2x RTX 5060 Ti lanes. The project also welcomes 3x/4x+, mixed 5060 Ti + CUDA, and other-CUDA community recipes when their topology and provenance are recorded clearly.

## Star History

<a href="https://www.star-history.com/?repos=5p00kyy%2Fclub-5060ti&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/chart?repos=5p00kyy/club-5060ti&type=date&theme=dark&legend=top-left&sealed_token=l_gzVshk3C_9akQK2SeItIrmti-0WmOsHYVDfwf7W3rdRm2MOg-TDSda9pM_DOUNTVRpEExIpsVPe5JukhUbbOjaTa-4uywVGnBUCN2iiRK_vRmNWxxJ_kfDzHv6zY5MGqBdS5zCmnU4SR0n6Tj4PrHv9PujeOEOiHt8Ji7EhzyaCZZ1vHmAwjVfgWk6" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/chart?repos=5p00kyy/club-5060ti&type=date&legend=top-left&sealed_token=l_gzVshk3C_9akQK2SeItIrmti-0WmOsHYVDfwf7W3rdRm2MOg-TDSda9pM_DOUNTVRpEExIpsVPe5JukhUbbOjaTa-4uywVGnBUCN2iiRK_vRmNWxxJ_kfDzHv6zY5MGqBdS5zCmnU4SR0n6Tj4PrHv9PujeOEOiHt8Ji7EhzyaCZZ1vHmAwjVfgWk6" />
 <img alt="Star History Chart" src="https://api.star-history.com/chart?repos=5p00kyy/club-5060ti&type=date&legend=top-left&sealed_token=l_gzVshk3C_9akQK2SeItIrmti-0WmOsHYVDfwf7W3rdRm2MOg-TDSda9pM_DOUNTVRpEExIpsVPe5JukhUbbOjaTa-4uywVGnBUCN2iiRK_vRmNWxxJ_kfDzHv6zY5MGqBdS5zCmnU4SR0n6Tj4PrHv9PujeOEOiHt8Ji7EhzyaCZZ1vHmAwjVfgWk6" />
 </picture>
</a>

## Start Here

| Path | Use this when | Entry point |
| --- | --- | --- |
| Hardware lanes | You want to understand how 1x, 2x, 4x/multi, and other CUDA GPU results are separated. | docs/hardware-lanes.md |
| 1x RTX 5060 Ti | You want the best single-card fits and conservative starter configs. | docs/single-5060ti.md |
| 2x RTX 5060 Ti | You want dual-16GB GGUF or OpenAI-compatible vLLM recipes for 27B-class and long-context models. | docs/vllm-qwen38.md |
| Other CUDA GPUs | You want to adapt the recipes to non-5060 Ti or mixed-architecture NVIDIA setups. | docs/gpu-compatibility.md |
| Results explorer | You want to compare benchmark receipts, filter by tier, and inspect serving configs. | https://5p00kyy.github.io/club-5060ti/ |
| Benchmark protocol | You want to submit or compare a result without mixing methods. | docs/benchmark-protocol.md |
| Preset and evidence workflow | You want to test a preset without turning every raw run into a public result. | docs/preset-evidence-workflow.md |
| Submit a result | You want a quick structured contribution path. | docs/community-result-template.md |

## Current Direction

club-5060ti is a 5060 Ti project first, not specifically a dual-5060 Ti project. Single-card, dual-card, and larger community lanes are useful when labelled clearly. The public experience is being refreshed around a simple rule:

1. **Preset:** an exact, copyable configuration with a stated hardware lane and purpose.
2. **Evidence:** a compact reviewed bundle that validates useful context, retrieval, sustained generation, and caveats.
3. **Raw receipt:** local or archived diagnostic material, not a front-page recommendation.

The homepage starts with published presets and retains the results explorer for comparisons, experiments, and historical provenance. Imported llm-bench rows remain archived until they are rerun under the current protocol.

## Published Presets

| Lane | Preset | What was validated | Evidence |
| --- | --- | --- | --- |
| 2x RTX 5060 Ti | [Nail 35B-A3B Q4_K_XL](examples/llamacpp-nail-35b-a3b-dual-5060ti.ini) | 131K effective-context tier, two uncached 115K-token retrieval checks, and two ~92K-token sustained 512-token generations. | [Evidence bundle](data/evidence/nail-35b-a3b-q4-2x5060ti-131k.json) |
| 2x RTX 5060 Ti | [Muse Glimmer 30B dynamic Q4](examples/llamacpp-muse-glimmer-30b-dual-5060ti.ini) | 131K effective-context tier, two uncached 115K-token retrieval checks, and two ~92K-token sustained visible-answer generations with DFlash. | [Evidence bundle](data/evidence/muse-glimmer-30b-q4-dynamic-2x5060ti-131k.json) |
| 2x RTX 5060 Ti | [Qwen3.8 27B Q6_K](examples/llamacpp-qwen38-27b-dual-5060ti.ini) | **Recommended dual-card dense GGUF route.** 131K single-slot tier, two uncached ~115.4K-token retrieval checks, and two ~91.8K-token sustained runs that generated 3,072 tokens and reached visible answers with built-in MTP. | [Evidence bundle](data/evidence/qwen38-27b-q6-2x5060ti-131k.json) |
| 2x RTX 5060 Ti | [Qwen3.8 27B NVFP4 vLLM](examples/vllm-qwen38-27b-nvfp4.sh) | **Recommended OpenAI-compatible serving route.** 122,880-token single-slot tier, exact tool-call JSON, 49.1K-token marker retrieval, and three 118.7K-token streamed generations. Median: **952.50 tok/s prefill**, **67.29 tok/s decode**. | [Evidence bundle](data/evidence/qwen38-27b-nvfp4-vllm-2x5060ti-122k.json) |
| 2x RTX 5060 Ti | [ThinkingCap Qwen3.6 27B Q6_K](examples/llamacpp-thinkingcap-qwen36-27b-dual-5060ti.ini) | Alternative 131K single-slot route, with two uncached 115K-token retrieval checks and two ~92K-token sustained visible-answer generations using built-in MTP. | [Evidence bundle](data/evidence/thinkingcap-qwen36-27b-q6-2x5060ti-131k.json) |
| 1x RTX 5060 Ti | [ThinkingCap Qwen3.6 27B IQ3_M](examples/llamacpp-thinkingcap-qwen36-27b-single-5060ti.ini) | 64K tier, two uncached ~57.7K-token retrieval checks, and two ~45.9K-token sustained visible-answer generations with q8 KV and built-in MTP. | [Evidence bundle](data/evidence/thinkingcap-qwen36-27b-iq3m-1x5060ti-64k.json) |
| 1x RTX 5060 Ti | [Qwen3.8 27B IQ3_XXS](examples/llamacpp-qwen38-27b-single-5060ti.ini) | 64K tier, two uncached ~57.7K-token retrieval checks, and two ~45.9K-token sustained visible-answer generations with q8 KV and built-in MTP. | [Evidence bundle](data/evidence/qwen38-27b-iq3xxs-1x5060ti-64k.json) |
| 1x RTX 5060 Ti | [Nail 35B-A3B IQ3_XXS](examples/llamacpp-single-5060ti-qwen36-35b-a3b-iq3xxs.ini) | Configured 131K route with two uncached ~115.4K-token retrieval checks and two ~91.8K-token sustained visible-answer generations on the non-thinking request path; the endpoint did not expose active context metadata. | [Evidence bundle](data/evidence/nail-35b-a3b-iq3xxs-1x5060ti-131k.json) |

More cards are added only after their preset and evidence bundle meet the same standard.

## Preset Status

- **Recommended:** seed-tested, copyable preset with reviewed published evidence.
- **Alternative:** a useful documented route with a different trade-off.
- **Community-verified:** strong community evidence, not yet reproduced on the seed system.
- **Experimental:** useful but incomplete evidence or an intentionally exploratory trade-off.
- **Archived:** historical or superseded provenance.

These labels describe a preset. They do not turn every individual raw measurement into a recommendation.

## Tested Baseline

Seed hardware:

- GPUs: 2x NVIDIA GeForce RTX 5060 Ti 16GB
- Driver: 595.58.03
- Total VRAM: 32GB across two cards
- System: Dell Precision Tower 7810, Dell 0GWHMW board
- CPU: 2x Intel Xeon E5-2680 v4
- Host memory: 128GB DDR4-2133
- Inference environment: Proxmox LXC with 16 vCPU and 60GB RAM assigned
- PCIe link width: both RTX 5060 Ti cards run at x8 in this host
- Seed measurements taken with both cards' core/SM clock locked at 2300 MHz (power limit unchanged); throughput is specific to that operating point

See docs/hardware.md for the full baseline and hardware notes.

## Existing Recipe Index (Migration Inventory)

These older routes are useful source material while they are re-run or mapped to the new preset/evidence standard. Do not treat a row labelled “recommended” here as a replacement for a published preset card above.

| Lane | Model | Evidence | Notes |
| --- | --- | --- | --- |
| upstream llama.cpp | Qwen3.6 27B GGUF | Seed recipe | Previous-generation dual-card alternative. Q6_K at 131K ctx with f16 KV and MTP n=3 delivers 45-55 tok/s decode. Q3_K_XL on single card is the recommended budget fit at 204K ctx with q4 KV. |
| upstream llama.cpp | Qwen3.8 27B GGUF | Published evidence | Newest measured family. Single-card IQ3_XXS 64K q8 KV is the recommended one-card route. Dual-card Q6_K 131K f16 KV is the current recommended dense route, sustaining ~38.6 tok/s median decode at ~91.8K prompt tokens. See docs/llamacpp-qwen38.md. |
| upstream llama.cpp | Qwen3.5 9B GGUF | Seed recipe | Small long-context route; useful sanity lane for 1x and 2x cards. Recommended starter model on single card. |
| upstream llama.cpp | Qwen3.6 35B-A3B GGUF | Seed recipe | Strong MoE route. Recommended on both 1x (IQ3_XXS) and 2x (Q5_K_S) lanes. Fastest practical model in the dataset. |
| upstream llama.cpp | Qwen3.5 122B-A10B GGUF | Seed recipe | Stretch/large MoE. IQ4_XS on 2x cards with MTP n=4. Recommended for maximum parameter count. |
| upstream llama.cpp | Qwopus3.6 27B / 35B-A3B | Seed recipe | Fine-tune merge results. Capable tier; interesting alternative but not primary recs. |
| BeeLlama | Qwen3.6 27B / 35B-A3B DFlash | Exploratory seed rows | Single-card 27B Q3_K_XL 8K DFlash works; single-card 35B-A3B DFlash improves code-shaped output. Alternative engine, capable tier. |
| ik_llama.cpp | Qwen3.6 27B IQ4/IQ5 | Exploratory fit check | Single-card 105k q4-KV shape fits; clean benchmark rows need chat-template/no-thinking cleanup. |

## Results And Data

Published presets live under `data/presets/`; reviewed evidence lives under `data/evidence/`; historical benchmark rows remain in `data/results/` during the migration. New routine runs belong under `.local/bench/`, not `data/results/`.

Build the static site data:

~~~bash
python3 scripts/build_preset_data.py
python3 scripts/build_site_data.py
~~~

Validate preset, evidence, and historical result data:

~~~bash
python3 scripts/validate_presets.py data/presets
python3 scripts/validate_evidence.py data/evidence
python3 scripts/validate_results.py data/results
~~~

Run the high-context profile against an already-started preset route:

~~~bash
python3 scripts/run_high_context_profile.py \
  --base-url http://127.0.0.1:8080/v1 \
  --model Nail-35B-A3B \
  --preset nail-35b-a3b-q4-2x5060ti \
  --context-tokens 131072 \
  --disable-thinking
~~~

It writes a local receipt. Review it before deliberately promoting compact evidence. See [the preset and evidence workflow](docs/preset-evidence-workflow.md).

The old llm-bench summary rows have been imported into data/results/llm-bench-legacy-import.json as archived historical data (experimental tier). Rerun them under the benchmark protocol before using them for comparisons.

The hosted explorer shows model cards grouped by model and setup, with tier filtering, sparklines across prompt types, and serving config in the card subline. Generation tok/s is output-token speed; prompt eval tok/s is prompt/prefill processing speed. MTP/speculation and thinking mode are shown on each card and can be filtered. Enable "raw runs" in the explorer to inspect repeated measurements.

The Qwen3.6 27B Q6_K dual-card config (131K ctx, f16 KV, MTP n=3) benchmarks at 45-55 tok/s decode across standard prompt sets. The single-card Q3_K_XL config runs at 204K ctx with q4 KV cache.

The public catalogue grows by tested presets and compact evidence bundles, not by count of successful requests. Community reports can become a raw issue receipt, a reproduction of an existing preset, a new preset candidate, or archived provenance depending on completeness and comparability.

## Useful Next Data

The most useful new submissions are:

- 3x/4x+ RTX 5060 Ti results with full PCIe topology.
- Matched 2x RTX 5060 Ti no-MTP and MTP rows for the same 27B model, quant, context, and KV cache.
- Qwen3.6 35B A3B rows from different 5060 Ti systems, especially dual-card and larger-card-count setups.
- Matched Qwen3.8 vLLM MTP3/no-MTP rows at 8K, 32K, and 122K, with client-measured TTFT and streamed decode.
- Qwen3.8 27B single-card f16 KV 32K sustained-output checks.
- Single-card RTX 5060 Ti benchmarks (the 1x lane is growing but needs more coverage).
- Clearly labeled mixed-GPU or non-5060 Ti CUDA adaptation results.
- Power, thermal, and PCIe-link notes when they explain performance differences.

## Submit A Result

The preferred path is a GitHub issue using the result report template.

- Fast path: open an issue and paste the [copy-paste community result template](docs/community-result-template.md).
- Raw issue reports are also acceptable; include what you can, and maintainers can normalize missing fields.

At minimum include the hardware lane, exact GPU count, PCIe topology, runtime, model, quant, context, KV cache, generated-token count, prompt eval tok/s, decode tok/s, and caveats.

For a new preset candidate, use the appropriate workflow profile and attach the local receipt/review rather than committing routine rows into `data/results/`. See docs/preset-evidence-workflow.md and docs/reporting-results.md.

## Repo Map

- docs/benchmark-protocol.md - comparable-result rules, prompt sets, context tiers, and promotion levels
- docs/preset-evidence-workflow.md - canonical preset manifests, raw receipts, robust high-context fitting, and review
- docs/FAQ.md - short answers to common setup questions
- docs/community-goals.md - project goals and contribution priorities
- docs/client-examples.md - OpenAI-compatible client examples
- docs/reporting-results.md - how to capture a useful result report
- docs/hardware-lanes.md - how 1x, 2x, multi-5060 Ti, and other CUDA GPU results are separated
- docs/gpu-compatibility.md - Blackwell baseline, mixed-GPU, and other CUDA architecture notes
- docs/single-5060ti.md - conservative single-card starter configs
- docs/vllm-qwen38.md - current Qwen3.8 vLLM NVFP4/MTP preset and evidence
- docs/vllm-qwen36.md - historical Qwen3.6 vLLM notes
- docs/beellama-dflash.md - BeeLlama DFlash first-pass results and failure notes
- docs/ik-llama-cpp.md - ik_llama.cpp first-pass fit and protocol notes
- docs/llamacpp-qwen36.md - llama.cpp Qwen3.6 27B MTP GGUF route
- docs/llamacpp-qwen35-9b-mtp.md - Qwen3.5 9B native max-context route
- docs/qwen36-35b-a3b.md - Qwen3.6 35B A3B checks
- docs/qwen36-kv-quality-20260605.md - Qwen3.6 27B KV cache quality comparison
- docs/benchmarks.md - current human-readable result notes
- docs/troubleshooting.md - observed failures and fixes
- data/presets/ - canonical copyable preset manifests
- data/evidence/ - reviewed compact evidence bundles and public-safe receipts
- data/results/ - historical and explorer benchmark rows during migration
- examples/ - sanitized launch/config snippets
- scripts/ - validation, report, smoke, import, and benchmark helpers
- site/ - static results explorer generated from data/

## Model Downloads

The download helper wraps the Hugging Face CLI and accepts a Hugging Face author or organization, model repo name, optional quant/file selector, and optional download directory:

~~~bash
scripts/download-models.sh unsloth Qwen3.6-27B-MTP-GGUF Q4_K_XL ~/models/Qwen3.6-27B-MTP-GGUF
scripts/download-models.sh unsloth Qwen3.6-27B-MTP-GGUF Qwen3.6-27B-UD-Q6_K_XL.gguf ~/models/Qwen3.6-27B-MTP-GGUF
scripts/download-models.sh RedHatAI Qwen3.6-35B-A3B-NVFP4 '' ~/models/Qwen3.6-35B-A3B-NVFP4
~~~

When the selector ends in `.gguf`, it is treated as an exact file. Otherwise it becomes a GGUF include pattern, so `Q4_K_XL` downloads matching `*Q4_K_XL*.gguf` files. Leave the selector empty to download the full repository.

Install either the `hf` CLI or `huggingface-cli` before running it, and log in first when downloading gated models. Set `MODEL_DIR` if you want a different default root.

## llama.cpp Build Helper

~~~bash
scripts/update-llama.sh
~~~

This builds the upstream llama.cpp tree used by the Qwen3.6 GGUF examples. The helper is a reproducible public build path, not a service manager for a specific deployment.

The default CUDA architecture target is `120a` for RTX 5060 Ti / Blackwell. For other CUDA GPUs or mixed-architecture builds, pass the architectures explicitly:

~~~bash
CUDA_ARCHITECTURES="86;89;120a" scripts/update-llama.sh
~~~

Use the architecture list supported by your installed CUDA/CMake toolchain and record the exact value in your result. See docs/gpu-compatibility.md before treating mixed-card results as comparable with the 2x RTX 5060 Ti baseline.

## Contribution Standard

Contributions are most useful when they include exact GPU model, motherboard/PCIe layout, negotiated link width/generation, driver/runtime versions, launch commands, context length, KV cache settings, prompt shape, generated token count, tokens/sec, and relevant caveats.

Start with CONTRIBUTING.md and docs/benchmark-protocol.md.

## Verification

~~~bash
python3 -m py_compile scripts/*.py
bash -n scripts/*.sh examples/*.sh
python3 scripts/validate_presets.py data/presets
python3 scripts/validate_evidence.py data/evidence
python3 scripts/validate_results.py data/results
python3 scripts/build_preset_data.py
python3 scripts/build_site_data.py
./scripts/check_repo.sh
~~~
