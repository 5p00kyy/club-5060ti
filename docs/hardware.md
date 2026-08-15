# Tested Hardware

Initial results come from one dual-GPU Linux system.

| Component | Value |
| --- | --- |
| GPU | 2x NVIDIA GeForce RTX 5060 Ti |
| VRAM | 16GB per card, 32GB total |
| Driver | 595.58.03 |
| GPU architecture | Blackwell-class, compute 12.0 |
| System/chassis | Dell Precision Tower 7810 |
| Motherboard | Dell 0GWHMW |
| Host CPU | 2x Intel Xeon E5-2680 v4 |
| Host RAM | 128GB DDR4-2133 |
| Inference environment | Proxmox LXC |
| Inference CPU allocation | 16 vCPU |
| Inference RAM allocation | 60GB |
| PCIe link width | x8 on both RTX 5060 Ti cards |
| Seed GPU core/SM clock | Locked to 2300 MHz (2295 MHz driver readback) |
| GPU power limit | 180 W per card (stock/default) |
| Runtime style | Linux LXC, CUDA containers for vLLM |

## Seed GPU Operating Point

The reviewed August 2026 preset evidence was measured with both seed cards core/SM-clock locked to 2300 MHz for lower noise, thermals, and a repeatable operating point. The driver reports 2295 MHz because clocks are applied in hardware steps. The cards retained their stock 180 W power limit and did not use a memory overclock.

Treat throughput as specific to this quiet-clock seed baseline. Stock-boost or overclocked cards may differ; context fit and pass/fail evidence remain tied to the exact model, quant, KV cache, runtime, and serving configuration in each bundle. Community results should report their own clock and power state rather than inheriting the seed setting.

## PCIe Topology Matters

For multi-GPU inference, the slot wiring and negotiated link state can change how much tensor-parallel traffic hurts. A result from two cards at x16/x16 is not directly comparable to x16/x4 or x4/x4 without that context.

The seed setup has both RTX 5060 Ti cards running at x8 link width. Capture the full topology and link generation when possible:

~~~bash
nvidia-smi --query-gpu=index,name,pci.bus_id,pcie.link.gen.current,pcie.link.gen.max,pcie.link.width.current,pcie.link.width.max --format=csv
lspci -tv
sudo dmidecode -t system -t baseboard
~~~

The current seed benchmark rows are still useful as working recipe receipts. Treat PCIe-sensitive comparisons as host-specific unless the report includes slot wiring plus negotiated link width and generation.

## What Seems To Matter

- 16GB per card is tight for 27B-class models, so quantization and KV cache choices matter.
- Tensor parallel across both cards is the useful default for vLLM 27B NVFP4 serving.
- fp8 KV cache is important for long context experiments.
- Blackwell support is still moving quickly. Runtime version, container image, and CUDA architecture target matter more than they would on older, mature cards.
- Motherboard layout and PCIe link width/gen matter for community reports. Include them if you know them.
- Power limits and thermals matter for sustained decode. Include them when sharing numbers.

## Blackwell And Mixed-GPU Scope

The project name reflects the tested baseline, not a claim that every recipe is Blackwell-only. llama.cpp/GGUF results may transfer to other NVIDIA cards, especially when VRAM is similar, but mixed-architecture results should be reported separately from the 2x RTX 5060 Ti lane.

For non-5060 Ti or mixed-architecture builds, set the CUDA architectures explicitly when building llama.cpp, for example:

~~~bash
CUDA_ARCHITECTURES="86;89;120a" scripts/update-llama.sh
~~~

Use the architecture list supported by your installed CUDA/CMake toolchain. See docs/gpu-compatibility.md for the full caveats.

## What Not To Generalize Yet

- Single RTX 5060 Ti results may look very different.
- Mixed GPU results should be reported separately from dual-5060 Ti results.
- Motherboard PCIe layout may matter for multi-GPU setups.
- Different CPUs, RAM allocation, and host memory bandwidth may change long-context behavior.
- New vLLM, CUDA, and modelopt builds may change the best flags.

## Hardware Report Template

When sharing a result, this level of detail is enough to help others:

~~~text
GPU: 2x RTX 5060 Ti 16GB
Driver:
CPU:
Host RAM:
Inference/container RAM:
Motherboard:
PCIe layout/link width:
Core/SM clock or lock:
Power limits:
Runtime:
Model:
Context:
KV cache:
Decode tok/s:
Notes:
~~~
