# BeeLlama DFlash First Pass

BeeLlama is a llama.cpp fork with DFlash speculative decoding and Turbo/TCQ cache work. Treat this page as early recipe evidence for RTX 5060 Ti systems, not as a production recommendation.

Tested build:

- Runtime: BeeLlama `9459`, commit `07ac3cec6`.
- Build: CUDA 12.9, `GGML_CUDA=ON`, `GGML_CUDA_FA=ON`, `GGML_CUDA_FA_ALL_QUANTS=ON`, `CMAKE_CUDA_ARCHITECTURES=120a`.
- Hardware: seed Dell T7810 lane, RTX 5060 Ti 16GB, driver `595.58.03`.
- Target model family: Qwen3.6 27B GGUF.
- DFlash drafter source: `Anbeeld/Qwen3.6-27B-DFlash-GGUF`.

## What Worked

The stable positive row so far is a single-card, low-context lane:

| Lane | Target | Drafter | Context | KV | Prompt set | No-spec | DFlash |
| --- | --- | --- | ---: | --- | --- | ---: | ---: |
| 1x5060ti | Qwen3.6 27B `UD-Q3_K_XL` | none / IQ4_XS | 8192 | q4_0/q4_0 | short-chat | 21.71 tok/s | 43.49 tok/s |
| 1x5060ti | Qwen3.6 27B `UD-Q3_K_XL` | none / IQ4_XS | 8192 | q4_0/q4_0 | code-generate | 21.51 tok/s | 69.34 tok/s |
| 1x5060ti | Qwen3.6 27B `UD-Q3_K_XL` | none / IQ4_XS | 8192 | q4_0/q4_0 | agent-tool | 20.92 tok/s | 34.85 tok/s |

DFlash acceptance was workload-sensitive. The agent-tool run logged around `0.108` draft acceptance near the end of the run; the earlier 128-token smoke logged `0.142`. Even with low acceptance, code-shaped output improved strongly.

The benchmark rows are in `data/results/seed-beellama-qwen36-27b-20260523.json`.

## What Failed

Dual-card Q4_K_M target plus Q4_K_M DFlash drafter loaded at 32K context, but it was not a valid benchmark row. BeeLlama logged multi-GPU placement and then repeated drafter decode failures:

~~~text
DFlash: target=2 devices, drafter=2 devices
drafter decode failed
tokens of sequence 0 in the input batch have inconsistent sequence positions
~~~

The failed run fell below the no-spec baseline and was stopped. Do not cite it as DFlash speed.

Single-card IQ4_XS target plus IQ4_XS DFlash drafter at 32K context also failed to fit on a 16GB card. The target loaded with only about 429 MiB free, then the 892 MiB drafter allocation failed.

Single-card Q3_K_XL target plus IQ4_XS DFlash drafter at 32K context loaded, but a request OOMed during CUDA compute. Reducing to 8K context and `-b 512 -ub 128` produced the stable rows above.

## Local Multi-GPU Branch Follow-Up

A local BeeLlama branch was tested after the first pass: `fix/dflash-multigpu-seq-pos`.
The patch clears the DFlash drafter KV state on the CPU-ring fallback path before
building the next absolute-position draft batch. This is not upstreamed yet, so treat
these rows as branch evidence rather than a public recipe.

Test shape:

- Target: Qwen3.6 27B `Q4_K_M`.
- Drafter: Qwen3.6 27B DFlash `Q4_K_M`.
- Hardware: 2x RTX 5060 Ti 16GB.
- Context: 32768.
- KV: `q4_0/q4_0`.
- Split: layer split `1,1`.
- Batch: `-b 1024 -ub 256`.

The useful result is correctness, not a clean speed headline. The original dual-card
sequence-position failure did not reproduce across the valid branch matrix: no
`drafter decode failed` or inconsistent sequence-position errors appeared.

| Config | short-chat | code-generate | agent-tool | Notes |
| --- | ---: | ---: | ---: | --- |
| no-spec Q4_K_M | 22.29 tok/s | 22.21 tok/s | 22.22 tok/s | Baseline, one measured run per prompt |
| DFlash `n4/x128` | 26.29 tok/s | 31.40 tok/s | 20.80 tok/s | First branch matrix pass |
| DFlash `n4/x128` repeat | 20.68 tok/s | 29.50 tok/s | 20.98 tok/s | Two measured runs per prompt |
| DFlash `n8/x128` rerun | 20.71 tok/s | 26.42 tok/s | 20.53 tok/s | Rerun after the first matrix row was interrupted |

Interpretation:

- The CPU-ring fallback patch is plausibly useful for upstream as a correctness fix.
- Performance is workload-sensitive and repeat-sensitive. Code generation improves,
  but short-chat and agent-tool are not consistently above no-spec.
- This should not be posted as a dual-5060 Ti DFlash speed win. It is better framed
  as "dual-GPU DFlash can be made correct on this branch, but CPU-ring fallback does
  not yet deliver a broad speedup."

## Qwen3.6 35B-A3B DFlash Pass

The same branch was also tested with Qwen3.6 35B-A3B on one RTX 5060 Ti.
This uses a matching 35B-A3B DFlash drafter; the 27B DFlash drafter is not
shape-compatible with the 35B-A3B target.

Test shape:

- Target: Qwen3.6 35B-A3B `UD-IQ3_XXS`.
- Drafter: Qwen3.6 35B-A3B DFlash `Q4_K_M`.
- Hardware: 1x RTX 5060 Ti 16GB.
- Context: 204800 for the short/code/tool rows.
- KV: `q8_0/q8_0`.
- Batch: `-b 2048 -ub 512`.
- DFlash: `--spec-draft-n-max 16 --spec-dflash-cross-ctx 512`,
  adaptive depth enabled.

| Config | Context | short-chat | code-generate | agent-tool | Notes |
| --- | ---: | ---: | ---: | ---: | --- |
| no-spec `UD-IQ3_XXS` | 204800 | 89.36 tok/s | 89.20 tok/s | 88.73 tok/s | Baseline |
| DFlash `n16/x512` | 204800 | 96.07 tok/s | 138.26 tok/s | 98.24 tok/s | Acceptance about 0.239 / 0.401 / 0.321 |

This is the first BeeLlama result here that looks genuinely interesting for a
single 5060 Ti: code-shaped output improved by about 55% over the no-spec
baseline while keeping q8 KV and a high configured context. Short-chat and
agent-tool improved more modestly.

Other 35B-A3B DFlash checks were less useful:

- Fixed `n16/x512` with adaptive depth disabled reached 152.47 tok/s on
  code-generate, but fell behind on short-chat and agent-tool.
- `n8/x512` adaptive was not better balanced than `n16/x512`.
- `x1024` GPU-ring cross context OOMed during decode on a 16GB card.
- A 204800-context long-retrieval prompt with 27061 prompt tokens OOMed during
  decode after prefill.

A lower-context long-retrieval check avoids the OOM, but it does not favor
DFlash:

| Config | CLI context | usable slot | Prompt tokens | Decode tok/s | Result |
| --- | ---: | ---: | ---: | ---: | --- |
| no-spec `UD-IQ3_XXS` | 65536 | 65536 | 27061 | 58.99 | Returned the needle |
| DFlash `n16/x512` | 65536 | 32768 | 27061 | 38.24 | Returned the needle, acceptance about 0.090 |

The DFlash long row used a 32768-token slot because this DFlash/recurrent setup
split the configured context across a backup cell. Treat these long rows as
short-answer fit/retrieval checks, not sustained decode benchmarks.

The benchmark rows are in
`data/results/seed-beellama-qwen36-35b-a3b-dflash-20260523.json`.

## Current Interpretation

BeeLlama DFlash is worth tracking for 5060 Ti users, but the tested useful shape is not yet the headline dual-5060 Ti lane. On this hardware:

- DFlash can materially improve a single-card 27B Q3_K_XL 8K route.
- A matching 35B-A3B DFlash drafter can materially improve the single-card
  35B-A3B `UD-IQ3_XXS` code-generation prompt at q8 KV.
- The public Reddit-style Q4/Q5 27B DFlash recipe does not directly transfer to split dual-16GB dense 27B serving as a speed result.
- The single-card 16GB fit margin is tight once the DFlash drafter is added.
- Code-shaped output benefits more than agent-tool or long-retrieval output in
  the measured rows.

Next useful sweeps:

- Test smaller `--spec-draft-n-max` values such as 4 and 8.
- Try `--spec-dm-adaptive` again after a stable baseline, but keep logs for acceptance and decode failures.
- Test 16K with Q3_K_XL, lower `-ub`, and `cross_ctx=512`.
- For dual-GPU, the next real speed work is GPU-ring hidden capture or a better adaptive policy, not just larger CPU-ring draft depth.
