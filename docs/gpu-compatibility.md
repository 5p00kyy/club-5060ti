# GPU Compatibility Notes

club-5060ti is tested around RTX 5060 Ti 16GB cards, but not every note here is Blackwell-only. Treat the 5060 Ti results as the baseline hardware lane, then report other NVIDIA cards as separate lanes instead of mixing them into the headline numbers.

## What Is 5060 Ti Specific?

- The checked-in benchmark rows use one or two RTX 5060 Ti 16GB cards unless marked otherwise.
- The default llama.cpp build helper targets Blackwell with `CUDA_ARCHITECTURES=120a`.
- The vLLM NVFP4/MTP examples are Blackwell-oriented and should not be assumed to work unchanged on older cards.
- The memory-fit notes depend on 16GB per card, PCIe layout, driver/runtime version, and the exact quant/KV cache settings.

## What May Generalize?

- GGUF/llama.cpp recipes often transfer better than vLLM NVFP4 recipes, especially when the cards have similar VRAM.
- Benchmark reporting rules apply to any local GPU setup: record model, quant, context, generated tokens, KV cache, runtime, driver, and hardware topology.
- Single-card and mixed-card results are useful, but they should be labeled separately from the 1x/2x RTX 5060 Ti lanes.

## Mixed Or Non-Blackwell CUDA Setups

Other NVIDIA CUDA GPUs may work with parts of the repo, especially the llama.cpp/GGUF recipes. Mixed-architecture setups may also work, but expect a different best tensor split and do not assume the dual-5060 Ti numbers apply.

Start with llama.cpp before vLLM for mixed-card or non-Blackwell testing:

~~~bash
CUDA_ARCHITECTURES="86;89;120a" scripts/update-llama.sh
~~~

That example is only illustrative. Set a semicolon-separated CMake CUDA architecture list that matches the GPUs you want the binary to support. If your CUDA/CMake toolchain rejects an architecture string, use the architecture names supported by your installed toolchain and record the exact value in your result.

Then test a conservative GGUF route before raising context or adding speculative decoding:

~~~bash
CUDA_VISIBLE_DEVICES=0,1 ./llama serve \
  --model /path/to/model.gguf \
  --ctx-size 32768 \
  --cache-type-k q8_0 \
  --cache-type-v q8_0 \
  --tensor-split 1,1
~~~

Adjust `--tensor-split` for the actual cards. Equal VRAM does not guarantee equal speed, and unequal cards may need an uneven split.

## vLLM Caveat

vLLM tensor parallel and NVFP4/MTP paths are stricter than llama.cpp/GGUF paths. A setup that works with two identical RTX 5060 Ti cards may fail or underperform on another architecture or mixed-card system because the kernel, quantization, and runtime assumptions are different.

If you test vLLM on mixed cards, report it as its own engine lane and include:

- exact GPU names and VRAM;
- driver, CUDA, PyTorch, and vLLM versions;
- tensor parallel size;
- model/quant source;
- KV cache dtype;
- whether startup, health check, and generation all passed.

## Reporting Rule

Do not collapse mixed-card results into the 2x RTX 5060 Ti baseline. They are valuable, but they answer a different question.
