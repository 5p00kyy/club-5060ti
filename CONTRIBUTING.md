# Contributing

Good contributions make the setup easier to reproduce.

Raw issue reports are welcome.
If you do not have all fields, include what you have and maintainers can normalize missing details into the expected submission format.

Please include:

- hardware lane: 1x 5060 Ti, 2x 5060 Ti, 3x+ 5060 Ti, mixed 5060 Ti plus other CUDA GPUs, or other CUDA GPU comparison
- GPU model and VRAM, including whether it is one card or multiple cards
- CPU, host RAM, inference/container RAM allocation, motherboard, and PCIe slot/link details if long context or multi-GPU performance matters
- driver version
- runtime and runtime version or commit
- model, quant, and source
- exact launch command or config
- context length and KV cache dtype
- tensor parallel or split settings
- benchmark prompt length and generated token count
- tokens/sec and whether it is prompt, decode, or end-to-end
- caveats and warnings

Do not paste API keys, private IP addresses, private hostnames, full logs with secrets, or benchmark claims without enough setup detail.
