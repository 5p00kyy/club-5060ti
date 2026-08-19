# Hardware Lanes

club-5060ti is organized around RTX 5060 Ti 16GB cards, not one exact machine. Results should be grouped by hardware lane so a single-card fit check, a dual-card recipe, and a quad-card experiment can all be useful without being treated as the same benchmark.

## Lanes

| Lane | Use for | Compare with |
| --- | --- | --- |
| 1x RTX 5060 Ti 16GB | Single-card fits, conservative GGUF recipes, small/medium models, lower-context checks | Other 1x 5060 Ti results with similar runtime/model settings |
| 2x RTX 5060 Ti 16GB | Current seed baseline, dual-16GB recipes, tensor split/tensor parallel checks | Other 2x 5060 Ti systems with similar PCIe topology and runtime settings |
| 3x+ RTX 5060 Ti 16GB | Community three-or-more-card setups, larger context/model-fit experiments, scaling checks | Other 5060 Ti systems with the same GPU count where possible |
| Mixed RTX 5060 Ti plus other CUDA GPUs | Adaptation experiments and practical mixed-card reports | Mixed-GPU reports with clearly labeled GPU models and split settings |
| Other CUDA GPUs | Nearby comparison data and recipe adaptation | Other reports in the same GPU family/count, not the 5060 Ti headline lanes |

## Why Lanes Matter

More cards do not automatically mean a comparable result. Multi-GPU inference can be limited by PCIe topology, runtime support, tensor split, tensor parallel behavior, batch shape, and the slowest card in the set. A quad 5060 Ti report is valuable, but it answers a different question than the current 2x seed baseline.

## What To Report

For every lane, include:

- GPU count, exact GPU model names, and VRAM per GPU;
- motherboard/system, CPU, host RAM, and inference/container RAM;
- PCIe link width and generation for each GPU;
- driver, CUDA, runtime, and runtime version or commit;
- model, quant, context length, KV cache, and generated-token budget;
- tensor split, tensor parallel size, GPU layer split, or equivalent placement settings;
- prompt eval tok/s, generation tok/s, wall time if available, and VRAM per GPU;
- whether the result is a clean benchmark, a fit check, a failure, or a partial/offload run.

Failures are useful when they include the setup and the last meaningful error. Do not only report successful launches.

## Promotion Rule

A result can be archived for provenance even if it is incomplete. It should only be promoted into comparison tables when its hardware lane and benchmark method are clear enough for someone else to reproduce.
