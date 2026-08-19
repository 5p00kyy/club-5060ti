# Reporting Results

A useful result is reproducible. A vague tok/s number is not.

## Quick Start

~~~bash
python3 scripts/run_openai_bench.py \
  --base-url http://127.0.0.1:8000/v1 \
  --model your-model-id \
  --prompt-set short-chat \
  --prompt-set code-generate \
  --prompt-set agent-tool \
  --runs 1 \
  --no-thinking \
  --tier capable \
  --output data/results/community-my-run.json \
  --report-output my-result.md
~~~

Validate before submitting:

~~~bash
python3 scripts/validate_results.py data/results/community-my-run.json
~~~

New measured results default to the `capable` tier. `recommended` is a maintainer decision for the best current speed/fit recipe in a lane, while `experimental` is for incomplete or unusual work. A submitted row can be published in the results catalogue when it is accepted and schema/protocol complete; `verified` means independently reproduced, and `recommended` remains curated. Routine maintainer runs stay under `.local/bench/` until deliberately accepted for publication.

If you cannot produce structured JSON right away, open a raw result issue and fill what you can.
Use the copy/paste issue-ready format in [docs/community-result-template.md](community-result-template.md), and the maintainer can normalize missing fields.

For full JSON submissions, keep using
`.github/ISSUE_TEMPLATE/result-report.md` as the preferred issue format.

If you want a hardware/endpoint report block:

~~~bash
bash scripts/report.sh --url http://127.0.0.1:8000 --model your-model-id >> my-result.md
~~~

report.sh redacts common secrets, private IPs, and URL hosts from command output. Still review the final text manually.

## Include These Details

- hardware lane: 1x 5060 Ti, 2x 5060 Ti, 3x+ 5060 Ti, mixed 5060 Ti plus other CUDA GPUs, or other CUDA GPU comparison
- GPU model and count
- VRAM per GPU
- driver version
- CPU, host RAM, inference/container RAM allocation, and motherboard/system model
- PCIe slot layout and negotiated link width/gen per GPU
- OS/container setup
- runtime and version (including Ollama, which is a distinct engine lane from raw llama.cpp)
- model and quant
- launch command or config
- context length
- KV cache dtype
- tensor parallel or tensor split
- generated token count
- decode tok/s
- warnings, restarts, or caveats
- anything unusual that affects reproducibility

If the result is from three or more 5060 Ti cards, mixed GPUs, or non-5060 Ti hardware, say that plainly in the title or first paragraph. It is useful data, but it should not be blended into the 2x RTX 5060 Ti baseline.

## Issue Reports

For runtime or client problems, include the exact command/config, the last meaningful error, whether a basic chat completion still works, and whether the issue changes between single-GPU and multi-GPU launch modes.
