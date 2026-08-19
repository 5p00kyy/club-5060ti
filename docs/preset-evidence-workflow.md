# Preset And Evidence Workflow

club-5060ti publishes **tested presets**, not every successful benchmark request.

A preset is a configuration someone can copy and use. Evidence is the compact,
reviewed proof that it fits its stated hardware lane and use case. Raw benchmark
receipts remain useful, but they are local until a maintainer deliberately
promotes an evidence bundle.

## Data Boundaries

| Location | Purpose | Published to Pages? |
| --- | --- | --- |
| `examples/` | Copyable llama.cpp and engine presets | Linked from docs/cards |
| `data/presets/` | Canonical preset manifests | Yes, after site migration |
| `.local/bench/` | Raw runs, retries, failures, and local reviews | No |
| `data/evidence/` | Reviewed evidence candidates and promoted bundles | Yes, after promotion |
| `data/results/` | Accepted published benchmark submissions and historical provenance | Current explorer only during migration |

Do not write a new routine maintainer run into `data/results/` just because it
completed. Accepted community submissions may be published there once their
validated result data and provenance are reviewed; publication does not mean
the maintainer reproduced the run.

## High-Context Fit

The `high-context` profile validates one unchanged serving preset at a time. It
walks a declared context ladder rather than treating one failed high tier as a
model-wide fit verdict.

At each tier the server must already be launched with that exact context. The
profile then performs uncached retrieval and sustained-generation checks. Every
request includes a unique leading nonce as well as `cache_prompt: false`, so a
server's longest-common-prefix reuse cannot make repeated synthetic prompts look
like fresh prefills. It records actual prompt tokens, prompt/prefill speed,
decode speed, output length, and failures.

A tier is useful only when it:

- reaches the required fraction of its configured context with an uncached prompt;
- passes repeated retrieval checks;
- passes repeated sustained-generation checks with enough client-visible final content;
- sustains the profile's minimum decode speed.

Failures are diagnostic. A failure at 131K does not invalidate a 96K result. The
review script selects the highest passing tier and keeps higher failures visible.

The runner never changes quant, KV type, CPU offload, speculation, or other
quality-affecting settings to make a tier fit. Those are new preset candidates.
If a preset deliberately runs non-thinking, pass `--disable-thinking` and record
that request-level template setting in the preset manifest. The runner validates
the client-visible final answer separately from `reasoning_content`: a model that
spends its whole output budget reasoning and produces no final answer has not
passed retrieval or useful sustained generation. Never silently hide reasoning
merely to make retrieval look clean.

The sustained output allowance is deliberately larger than the minimum generated-work threshold. This gives thinking-heavy models enough room to finish hidden reasoning and still return a client-visible answer without forcing concise models to consume the entire allowance.

## Run A Profile

First validate the preset manifest:

~~~bash
python3 scripts/validate_presets.py data/presets/nail-35b-a3b-iq3xxs-1x5060ti.json
~~~

Launch the server using the selected preset and context tier. Then run a single
tier. The profile first sends small uncached calibration requests against the
actual tokenizer, estimates the filler needed, and corrects it before the real
checks. It aims slightly above each minimum prompt fraction so nonce and tokenizer
variation cannot turn an otherwise valid repeated check into a one-token miss.
It will not claim a configured context from character-count guesswork.

~~~bash
python3 scripts/run_high_context_profile.py \
  --base-url http://127.0.0.1:8080/v1 \
  --model Nail-35B-A3B-IQ3_XXS \
  --preset nail-35b-a3b-iq3xxs-1x5060ti \
  --context-tokens 131072
~~~

Raw receipts go to `.local/bench/` and are ignored by Git. Repeat at lower or
higher declared tiers as appropriate. A failed tier returns exit code `2`, but
still writes its receipt.

For a fresh dedicated test server, the ladder script can launch one isolated
server process per tier and stop only the process it owns. The launch template
must visibly contain `{context_tokens}`, which prevents a hidden setting change
from being mistaken for a result. It refuses to use an endpoint already serving
the target model, so it cannot replace a shared router/service.

~~~bash
python3 scripts/run_context_ladder.py \
  --base-url http://127.0.0.1:18081/v1 \
  --model Nail-35B-A3B-IQ3_XXS \
  --preset nail-35b-a3b-iq3xxs-1x5060ti \
  --server-command-template 'llama-server --model /models/nail.gguf --ctx-size {context_tokens} --cache-type-k q8_0 --cache-type-v q8_0 --n-gpu-layers 99 --port 18081'
~~~

By default, the ladder stops after the first unusable tier and the review still
selects the highest lower passing tier. Use `--keep-going` only for diagnostic
work; it does not turn a failed tier into a viable result. Use `--start-at` with
a declared rung when an existing reliable result already establishes the lower
bound, so a refresh can concentrate on the next meaningful range.

Review all receipts for that preset:

~~~bash
python3 scripts/review_context_fit.py \
  --preset nail-35b-a3b-iq3xxs-1x5060ti \
  --input .local/bench/nail-35b-a3b-iq3xxs-1x5060ti
~~~

This writes a local candidate review. It does not publish anything.

## Promotion

Promotion is a maintainer decision after inspecting the exact preset, raw
receipts, quality/caveat evidence, and whether the recipe genuinely improves the
community guide. A promoted bundle should describe the highest useful context,
median metrics, proof checks, caveats, and source receipts. `data/evidence/`
contains only reviewed candidate or published bundles, while raw receipts remain
local. `scripts/build_preset_data.py` builds compact preset cards from those
manifests without reading routine benchmark rows.

`recommended` is never assigned by the benchmark runner. Community submissions
may be published benchmark rows, reproduction evidence, or new preset candidates;
`verified` requires independent reproduction, while `recommended` is curated by
maintainers. Multi-GPU
community lanes are welcome, including 3x/4x+ and mixed CUDA systems, but must
record PCIe topology and tensor/TP configuration and are not presented as
seed-system reproductions.
