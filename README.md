# club-5060ti

Practical local LLM recipes, benchmark receipts, and setup notes for RTX 5060 Ti 16GB systems.

The project focus is simple: make RTX 5060 Ti local inference more reproducible across one card, two cards, and larger community setups. Some llama.cpp/GGUF notes are useful on other NVIDIA cards too, but non-5060 Ti and mixed-GPU results should be reported as separate hardware lanes. Every useful result should come with the launch shape, hardware context, model details, benchmark method, and caveats needed for someone else to reproduce or improve it.

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
| 2x RTX 5060 Ti | You want dual-16GB recipes for 27B-class and long-context models. | docs/llamacpp-qwen36.md |
| Other CUDA GPUs | You want to adapt the recipes to non-5060 Ti or mixed-architecture NVIDIA setups. | docs/gpu-compatibility.md |
| Results explorer | You want to compare benchmark receipts, filter by tier, and inspect serving configs. | https://5p00kyy.github.io/club-5060ti/ |
| Benchmark protocol | You want to submit or compare a result without mixing methods. | docs/benchmark-protocol.md |
| Submit a result | You want a quick structured contribution path. | docs/community-result-template.md |

## Current Direction

club-5060ti collects tested RTX 5060 Ti recipes and benchmark receipts. It is a 5060 Ti project first, not specifically a dual-5060 Ti project: single-card, dual-card, and larger 5060 Ti setups are all useful when labeled clearly. It is not meant to claim that only Blackwell cards can use these workflows; it keeps the 5060 Ti lanes clear so community results from other cards remain comparable instead of blended together. The results explorer is built from checked-in JSON under data/results/ so docs, scripts, and the static site all describe the same evidence.

Imported llm-bench rows are archived historical data until they are rerun under the benchmark protocol. They are useful provenance, not headline evidence.

## Tier System

Every benchmark result is assigned a tier to help visitors quickly find useful configs:

- **Recommended** - Best known speed/fit config for the GPU lane. Not a quality endorsement; it means this is the config to try first for that model and hardware.
- **Capable** - Works well as a solid option. Includes alternative quants, KV cache experiment variants, and fine-tune merges like Qwopus.
- **Experimental** - Stretch fits, unusual configs, and deprecated legacy imports. Interesting but not daily drivers.

Tiers can be filtered directly in the results explorer.

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

See docs/hardware.md for the full baseline and hardware notes.

## Recipe Index

| Lane | Model | Evidence | Notes |
| --- | --- | --- | --- |
| upstream llama.cpp | Qwen3.6 27B GGUF | Seed recipe | Recommended dual-card dense route. Q6_K at 131K ctx with f16 KV and MTP n=3 delivers 45-55 tok/s decode. Q3_K_XL on single card is the recommended budget fit at 204K ctx with q4 KV. |
| upstream llama.cpp | Qwen3.5 9B GGUF | Seed recipe | Small long-context route; useful sanity lane for 1x and 2x cards. Recommended starter model on single card. |
| upstream llama.cpp | Qwen3.6 35B-A3B GGUF | Seed recipe | Strong MoE route. Recommended on both 1x (IQ3_XXS) and 2x (Q5_K_S) lanes. Fastest practical model in the dataset. |
| upstream llama.cpp | Qwen3.5 122B-A10B GGUF | Seed recipe | Stretch/large MoE. IQ4_XS on 2x cards with MTP n=4. Recommended for maximum parameter count. |
| upstream llama.cpp | Qwopus3.6 27B / 35B-A3B | Seed recipe | Fine-tune merge results. Capable tier; interesting alternative but not primary recs. |
| BeeLlama | Qwen3.6 27B / 35B-A3B DFlash | Exploratory seed rows | Single-card 27B Q3_K_XL 8K DFlash works; single-card 35B-A3B DFlash improves code-shaped output. Alternative engine, capable tier. |
| ik_llama.cpp | Qwen3.6 27B IQ4/IQ5 | Exploratory fit check | Single-card 105k q4-KV shape fits; clean benchmark rows need chat-template/no-thinking cleanup. |
| vLLM | Qwen3.6 27B NVFP4/MTP | Comparison target | Historical notes exist, but this needs current benchmark JSON before promotion. |

## Results And Data

Canonical result files live under data/results/ and follow data/schema/benchmark-result.schema.json.

Build the static site data:

~~~bash
python3 scripts/build_site_data.py
~~~

Validate result JSON:

~~~bash
python3 scripts/validate_results.py data/results
~~~

Run a protocol-shaped OpenAI-compatible benchmark:

~~~bash
python3 scripts/run_openai_bench.py \
  --base-url http://127.0.0.1:8080/v1 \
  --model Qwen3.6-27B \
  --prompt-set short-chat \
  --prompt-set code-generate \
  --prompt-set agent-tool \
  --runs 1 \
  --no-thinking \
  --output data/results/my-run.json
~~~

The old llm-bench summary rows have been imported into data/results/llm-bench-legacy-import.json as archived historical data (experimental tier). Rerun them under the benchmark protocol before using them for comparisons.

The hosted explorer shows model cards grouped by model and setup, with tier filtering, sparklines across prompt types, and serving config in the card subline. Generation tok/s is output-token speed; prompt eval tok/s is prompt/prefill processing speed. MTP/speculation and thinking mode are shown on each card and can be filtered. Enable "raw runs" in the explorer to inspect repeated measurements.

The Qwen3.6 27B Q6_K dual-card config (131K ctx, f16 KV, MTP n=3) benchmarks at 45-55 tok/s decode across standard prompt sets. The single-card Q3_K_XL config runs at 204K ctx with q4 KV cache.

Results are expected to grow over time. New community reports can be added as archived notes, recipe evidence, benchmark rows, or verified reproductions depending on how complete and comparable they are.

## Useful Next Data

The most useful new submissions are:

- 3x/4x+ RTX 5060 Ti results with full PCIe topology.
- Matched 2x RTX 5060 Ti no-MTP and MTP rows for the same 27B model, quant, context, and KV cache.
- Qwen3.6 35B A3B rows from different 5060 Ti systems, especially dual-card and larger-card-count setups.
- Single-card RTX 5060 Ti benchmarks (the 1x lane is growing but needs more coverage).
- Clearly labeled mixed-GPU or non-5060 Ti CUDA adaptation results.
- Power, thermal, and PCIe-link notes when they explain performance differences.

## Submit A Result

The preferred path is a GitHub issue using the result report template.

- Fast path: open an issue and paste the [copy-paste community result template](docs/community-result-template.md).
- Raw issue reports are also acceptable; include what you can, and maintainers can normalize missing fields.

At minimum include the hardware lane, exact GPU count, PCIe topology, runtime, model, quant, context, KV cache, generated-token count, prompt eval tok/s, decode tok/s, and caveats.

If you want a structured result file, generate JSON with scripts/run_openai_bench.py, validate it with scripts/validate_results.py, and attach or submit the JSON. See docs/reporting-results.md.

## Repo Map

- docs/benchmark-protocol.md - comparable-result rules, prompt sets, context tiers, and promotion levels
- docs/FAQ.md - short answers to common setup questions
- docs/community-goals.md - project goals and contribution priorities
- docs/client-examples.md - OpenAI-compatible client examples
- docs/reporting-results.md - how to capture a useful result report
- docs/hardware-lanes.md - how 1x, 2x, multi-5060 Ti, and other CUDA GPU results are separated
- docs/gpu-compatibility.md - Blackwell baseline, mixed-GPU, and other CUDA architecture notes
- docs/single-5060ti.md - conservative single-card starter configs
- docs/vllm-qwen36.md - vLLM NVFP4/MTP notes
- docs/beellama-dflash.md - BeeLlama DFlash first-pass results and failure notes
- docs/ik-llama-cpp.md - ik_llama.cpp first-pass fit and protocol notes
- docs/llamacpp-qwen36.md - llama.cpp Qwen3.6 27B MTP GGUF route
- docs/llamacpp-qwen35-9b-mtp.md - Qwen3.5 9B native max-context route
- docs/qwen36-35b-a3b.md - Qwen3.6 35B A3B checks
- docs/qwen36-kv-quality-20260605.md - Qwen3.6 27B KV cache quality comparison
- docs/benchmarks.md - current human-readable result notes
- docs/troubleshooting.md - observed failures and fixes
- data/ - canonical result data and schemas
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
python3 scripts/validate_results.py data/results
python3 scripts/build_site_data.py
./scripts/check_repo.sh
~~~
