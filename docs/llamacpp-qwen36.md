# llama.cpp: Qwen3.6 27B MTP GGUF

This path is useful for GGUF workflows and for people who prefer llama.cpp-style serving.

## Important Requirement

Use a llama.cpp build that supports the Qwen3.6 MTP GGUF files. In testing, a regular upstream binary failed to load the MTP GGUF with this missing tensor error:

~~~text
missing tensor 'blk.64.ssm_conv1d.weight'
~~~

The current working setup uses upstream llama.cpp `9190 (b64739ea3)`, after Qwen3.6 MTP support from PR 22673 merged. Earlier seed results used PR-tip build `9032-5d5f1b46e`; keep benchmark rows tied to the exact runtime version.

The public helper scripts/update-llama.sh builds the tested upstream commit by default. Deployment wrappers vary by machine; the important reproducible pieces are the model path shape, build commit, CUDA flags, and preset settings below.

## MTP Flag Compatibility

Unsloth's 2026-05-15 update says newer Qwen3.6 MTP GGUF runs can benefit from `--spec-draft-p-min 0.75`, higher draft counts such as `--spec-draft-n-max 6`, and newer llama.cpp argument spelling around MTP.

Merged upstream llama.cpp `9190 (b64739ea3)` accepts `--spec-type draft-mtp`, `--spec-draft-p-min 0.75`, and `--spec-draft-n-max`. Older PR-tip seed results used `--spec-type mtp` on `9032-5d5f1b46e`. Do not mix those flag spellings without recording the build version.

## Working 96K-Class Preset

~~~ini
[Qwen3.6-27B]
model = /path/to/Qwen3.6-27B-UD-Q6_K_XL.gguf
ctx-size = 98304
cache-type-k = f16
cache-type-v = f16
n-gpu-layers = 99
split-mode = tensor
tensor-split = 50,50
temp = 0.7
top-k = 20
top-p = 0.95
min-p = 0
presence-penalty = 0.8
batch-size = 2048
ubatch-size = 512
spec-type = draft-mtp
spec-draft-p-min = 0.75
spec-draft-n-max = 3
jinja = on
parallel = 1
~~~

See examples/llamacpp-qwen36-preset.ini.

This is the recommended public long-context preset shape for the seed dual-card lane. Treat it as a 96K-class practical route: keep the actual prompt around 90-96K tokens, and leave part of that configured window for generated output. The benchmark row below was captured with the same Q6, f16 KV, split-mode tensor, tensor split 50,50, and MTP draft 3 route on 2x RTX 5060 Ti 16GB with upstream llama.cpp `9190 (b64739ea3)`.

For a lower-context serving preset with extra headroom, the example router shape keeps the same f16 KV + split-mode tensor + 50,50 split and uses 65536 context. See examples/llamacpp-qwen36-router.ini.

On this exact hardware/build lane (2x RTX 5060 Ti 16GB, upstream `9190/b64739ea3`), split `50,50` is the tested tensor route. Split `51,49` currently asserts in tensor mode and should not be treated as equivalent.

## Observed Q4 vs Q6 Benchmark

Test shape:

- llama.cpp MTP-capable build
- 2x RTX 5060 Ti 16GB
- 8K context
- q8 KV
- tensor split 1,1
- 768 generated tokens

| Quant | MTP | Decode |
| --- | --- | --- |
| Q4 | off | 21.31 tok/s |
| Q4 | draft 2 | 34.63 tok/s |
| Q6 | off | 15.61 tok/s |
| Q6 | draft 2 | 27.33 tok/s |

Q6 fit GPU-only at 8K in testing, but it was tighter on VRAM and slower than Q4. Treat Q6 as a quality/speed tradeoff, not a straight replacement.

## Merged Upstream Draft Count Check

After PR 22673 merged, upstream llama.cpp `9190 (b64739ea3)` was checked with Qwen3.6 27B MTP Q6 at 8K context, q8 KV, tensor split 1,1, `--fit off`, and 384 generated tokens.

| MTP | Decode | Draft acceptance |
| --- | --- | --- |
| off | 15.66 tok/s | n/a |
| draft 2, p-min 0.75 | 28.34 tok/s | 0.704 |
| draft 3, p-min 0.75 | 30.46 tok/s | 0.628 |
| draft 6, p-min 0.75 | 23.64 tok/s | 0.345 |

For this Q6 test, draft 3 beat draft 2 and draft 6. The larger draft-6 window generated more draft tokens, but acceptance fell enough to lose throughput.

## Historical Router Result

Earlier 65536-context router checks on q8 KV + layer-split shapes measured 32.04 tok/s with draft 2 and 37.48 tok/s with draft 3 over 64 generated tokens. Keep those as historical comparison points; the current recommended route for this doc is f16 KV with split-mode tensor and split `50,50`.

## Observed Long-Context Generation Result (f16 Tensor 50,50)

Seed benchmark row on upstream llama.cpp `9190 (b64739ea3)`, Qwen3.6 27B Q6_K_XL, `ctx=184320`, f16 KV, split-mode tensor, split `50,50`, draft-mtp n=3 p-min=0.75:

- Prompt set: `custom` (`long-context-generate`)
- Actual prompt tokens: `87293`
- Generated tokens: `742`
- Prompt eval: `420.14 tok/s`
- Decode: `21.73 tok/s`
- Draft acceptance: `0.43582`

This row is the sustained long-context generation reference for this lane because it combines >80k prompt tokens with a multi-hundred-token completion. Use it as the practical 96K-class claim for this hardware, not as evidence that the full configured context remains fast.

## Observed Long-Retrieval Result (f16 Tensor 50,50)

Seed benchmark row on upstream llama.cpp `9190 (b64739ea3)`, Qwen3.6 27B Q6_K_XL, `ctx=184320`, f16 KV, split-mode tensor, split `50,50`, draft-mtp n=3 p-min=0.75:

- Prompt set: `long-retrieval` (scaled synthetic filler)
- Actual prompt tokens: `90061`
- Generated tokens: `17`
- Prompt eval: `514.65 tok/s`
- Decode: `15.29 tok/s`
- Draft acceptance: `1.0` (`17/17` in this short-answer run)

This row is a long-context stability/fit check with >80k prompt tokens. Because the retrieval answer is intentionally short, treat decode speed as a short-answer data point only, not a sustained decode ceiling.

## 150K+ Diagnostic

Follow-up diagnostics with prompts around 151K actual prompt tokens could prefill on this f16 tensor route, but sustained decode fell to roughly 0.36-0.43 tok/s. That shape is useful as a fit/failure boundary, not as a public performance result. Do not promote 150K+ prompt-token runs for this lane unless a future runtime or serving shape fixes the decode collapse.

## Observed Normal-Generation Result (same lane)

Seed benchmark fact for the same hardware/runtime/model route, imported from a same-host parent-session run:

- Prompt shape: `p1k/n512` (`custom` prompt set)
- Actual prompt tokens: `1621`
- Generated tokens: `512`
- Prompt eval: `183.84 tok/s`
- Decode: `52.43 tok/s`
- Draft acceptance: `0.75159` (draft-mtp n=3, p-min=0.75)

This row is included to represent normal generation throughput and should be compared separately from the short-answer long-retrieval stability row.

## Historical Q6 q8 Context Fit

The Q6 q8/q8 llama.cpp MTP setup loaded and completed chat checks at:

| Context | Result |
| --- | --- |
| 65,536 | chat OK |
| 98,304 | chat OK |
| 131,072 | chat OK |
| 160,000 | chat OK |
| 180,000 | chat OK |
| 200,000 | chat OK |

Before the f16 tensor migration, merged upstream llama.cpp `9190 (b64739ea3)` recovered a needle from an 87031-token prompt at both 200000 and 204800 context with q8 KV and `draft-mtp` n=3. Those runs reached about 15847 MiB on GPU0 and 15825 MiB on GPU1 during the request. Keep them as historical evidence; current recommendation in this guide is the f16 tensor `50,50` route as a 96K-class practical long-context lane.

## Caveats

- Do not assume draft/speculative decoding is working just because flags are present. Check logs for real MTP/speculative acceptance.
- Treat MTP flag names as build-specific. Current upstream examples use `--spec-type draft-mtp`; older seed rows in this repo used `--spec-type mtp` on the pre-merge PR-tip build.
- Older speculative paths for recurrent/hybrid Qwen models can produce corrupt output. Avoid unsafe pre-guard builds unless you are explicitly experimenting.
- Keep one clean preset per model family. Swap the quant path instead of accumulating many stale preset sections.
