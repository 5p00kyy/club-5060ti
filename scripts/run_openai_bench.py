#!/usr/bin/env python3
import argparse
import json
import os
import re
import secrets
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


PROMPT_SET_CHOICES = ("short-chat", "code-generate", "agent-tool", "tool-call", "long-retrieval", "custom")
CACHE_POLICIES = ("server-default", "no-reuse")
TOOL_NAME = "record_benchmark_note"


def build_prompts(long_retrieval_filler_lines=900, long_retrieval_max_tokens=96):
    return {
        "short-chat": {
            "max_tokens": 256,
            "text": "Write a practical checklist for validating a local OpenAI-compatible LLM server. Keep it concise.",
        },
        "code-generate": {
            "max_tokens": 768,
            "text": (
                "Write a Python module that validates benchmark result dictionaries for required keys, "
                "normalizes model names into URL-safe slugs, and prints a compact summary table. "
                "Include type hints and a small __main__ example."
            ),
        },
        "agent-tool": {
            "max_tokens": 512,
            "text": (
                "You are reviewing a local LLM benchmark report for publication. "
                "Tool output: GPU0 RTX 5060 Ti 16GB x8, GPU1 RTX 5060 Ti 16GB x8, driver 595.58.03, "
                "runtime llama.cpp, model Qwen3.6 27B, q8 KV, draft-MTP enabled. "
                "List the missing details that must be captured before this result can be compared publicly."
            ),
        },
        "tool-call": {
            "max_tokens": 128,
            "text": (
                "Use the record_benchmark_note tool exactly once. Record the note "
                "'vLLM tool-call contract passed' with severity 'info'. "
                "Do not answer with prose before or instead of the tool call."
            ),
            "tools": [{
                "type": "function",
                "function": {
                    "name": TOOL_NAME,
                    "description": "Record a deterministic benchmark contract note.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "note": {"type": "string"},
                            "severity": {"type": "string", "enum": ["info", "warning"]},
                        },
                        "required": ["note", "severity"],
                        "additionalProperties": False,
                    },
                },
            }],
            "tool_choice": {"type": "function", "function": {"name": TOOL_NAME}},
        },
        "long-retrieval": {
            "max_tokens": long_retrieval_max_tokens,
            "text": (
                "You are checking retrieval from a long synthetic context. "
                "Remember this key exactly: CLUB-5060TI-NEEDLE-194.\n\n"
                + (
                    "Filler block: local inference benchmark notes need hardware, runtime, model, quant, context, KV cache, generated tokens, and caveats.\n"
                    * long_retrieval_filler_lines
                )
                + "\nQuestion: what exact key were you told to remember? Reply with only the key."
            ),
        },
    }

SOURCE_TYPES = {"seed", "community", "imported", "external"}
TIERS = {"recommended", "capable", "experimental"}
HARDWARE_LANES = {"1x5060ti", "2x5060ti", "multi-5060ti", "mixed-5060ti-cuda", "other-cuda", "unknown"}


def slugify(value):
    value = value.lower()
    value = re.sub(r"[^a-z0-9._-]+", "-", value)
    value = value.strip("-")
    return value or "result"


def post_json(url, payload, timeout, api_key=None, extra_headers=None):
    data = json.dumps(payload).encode("utf-8")
    headers = {"content-type": "application/json"}
    if api_key:
        headers["authorization"] = f"Bearer {api_key}"
    if extra_headers:
        headers.update(extra_headers)
    req = urllib.request.Request(
        url,
        data=data,
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def get_json(url, timeout, api_key=None):
    headers = {}
    if api_key:
        headers["authorization"] = f"Bearer {api_key}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def iter_sse_events(chunks):
    """Yield decoded SSE data payloads from arbitrarily fragmented chunks."""
    buffer = ""
    for chunk in chunks:
        if isinstance(chunk, bytes):
            chunk = chunk.decode("utf-8", errors="replace")
        buffer += chunk
        while True:
            match = re.search(r"\r?\n\r?\n", buffer)
            if not match:
                break
            event, buffer = buffer[:match.start()], buffer[match.end():]
            data_lines = []
            for line in event.splitlines():
                if line.startswith("data:"):
                    data_lines.append(line[5:].lstrip())
            if data_lines:
                yield "\n".join(data_lines)
    if buffer.strip():
        data_lines = [line[5:].lstrip() for line in buffer.splitlines() if line.startswith("data:")]
        if data_lines:
            yield "\n".join(data_lines)


def _merge_tool_delta(tool_calls, delta_calls):
    for delta in delta_calls or []:
        index = int(delta.get("index", 0))
        while len(tool_calls) <= index:
            tool_calls.append({"id": "", "type": "function", "function": {"name": "", "arguments": ""}})
        target = tool_calls[index]
        if delta.get("id"):
            target["id"] = delta["id"]
        if delta.get("type"):
            target["type"] = delta["type"]
        function = delta.get("function") or {}
        if function.get("name"):
            target["function"]["name"] = function["name"]
        target["function"]["arguments"] += function.get("arguments") or ""


def parse_sse_events(payloads):
    """Aggregate OpenAI chat SSE events, tolerating malformed non-events."""
    content, reasoning, tool_calls, usage = "", "", [], {}
    first_output = False
    for payload in payloads:
        if payload == "[DONE]":
            continue
        try:
            event = json.loads(payload)
        except json.JSONDecodeError:
            continue
        if event.get("usage"):
            usage = event["usage"]
        for choice in event.get("choices") or []:
            delta = choice.get("delta") or {}
            content += delta.get("content") or ""
            reasoning += delta.get("reasoning_content") or delta.get("reasoning") or ""
            _merge_tool_delta(tool_calls, delta.get("tool_calls"))
            if delta.get("content") or delta.get("reasoning_content") or delta.get("reasoning") or delta.get("tool_calls"):
                first_output = True
    message = {"content": content}
    if reasoning:
        message["reasoning_content"] = reasoning
    if tool_calls:
        message["tool_calls"] = tool_calls
    return {"choices": [{"message": message}], "usage": usage, "timings": {}}, first_output


def post_stream_json(url, payload, timeout, api_key=None, metrics_url="", extra_headers=None):
    """Return response plus client observations; never label them server prefill."""
    payload = dict(payload)
    payload["stream"] = True
    payload["stream_options"] = {"include_usage": True}
    headers = {"content-type": "application/json", "accept": "text/event-stream"}
    if api_key:
        headers["authorization"] = f"Bearer {api_key}"
    if extra_headers:
        headers.update(extra_headers)
    before = snapshot_prometheus(metrics_url, timeout, api_key)
    started = time.monotonic()
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as response:
        # HTTPResponse.read(n) may wait for n bytes and destroy TTFT. read1(n)
        # returns currently available streamed bytes while retaining arbitrary
        # chunk-boundary handling in the SSE parser.
        read_chunk = getattr(response, "read1", response.read)
        chunks = iter(lambda: read_chunk(4096), b"")
        first_output_at = None
        payloads = []
        # Parse incrementally so TTFT is measured at the first meaningful delta.
        buffer = ""
        for chunk in chunks:
            if not chunk:
                break
            buffer += chunk.decode("utf-8", errors="replace")
            while True:
                match = re.search(r"\r?\n\r?\n", buffer)
                if not match:
                    break
                event, buffer = buffer[:match.start()], buffer[match.end():]
                data_lines = [line[5:].lstrip() for line in event.splitlines() if line.startswith("data:")]
                if not data_lines:
                    continue
                data = "\n".join(data_lines)
                payloads.append(data)
                if first_output_at is None and data != "[DONE]":
                    try:
                        parsed = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                    for choice in parsed.get("choices") or []:
                        delta = choice.get("delta") or {}
                        if delta.get("content") or delta.get("reasoning_content") or delta.get("reasoning") or delta.get("tool_calls"):
                            first_output_at = time.monotonic() - started
                            break
        if buffer.strip():
            payloads.extend(iter_sse_events([buffer]))
    elapsed = time.monotonic() - started
    response, _ = parse_sse_events(payloads)
    usage = response.get("usage") or {}
    completion_tokens = usage.get("completion_tokens")
    decode_seconds = elapsed - first_output_at if first_output_at is not None else None
    client = {
        "client_ttft_seconds": round(first_output_at, 3) if first_output_at is not None else None,
        "client_decode_tok_s": round(completion_tokens / decode_seconds, 3) if completion_tokens and decode_seconds and decode_seconds > 0 else None,
        "client_end_to_end_tok_s": round(completion_tokens / elapsed, 3) if completion_tokens and elapsed > 0 else None,
    }
    client.update(server_metric_rates(before, snapshot_prometheus(metrics_url, timeout, api_key)))
    return response, elapsed, client


def snapshot_prometheus(url, timeout, api_key=None):
    if not url:
        return {}
    try:
        text = get_text(url, timeout, api_key)
    except Exception:
        return {}
    values = {}
    for line in text.splitlines():
        if not line or line.startswith("#") or " " not in line:
            continue
        name, raw = line.rsplit(None, 1)
        try:
            values[name.split("{", 1)[0]] = values.get(name.split("{", 1)[0], 0.0) + float(raw)
        except ValueError:
            continue
    return values


def get_text(url, timeout, api_key=None):
    headers = {"authorization": f"Bearer {api_key}"} if api_key else {}
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def server_metric_rates(before, after):
    if not before or not after:
        return {}
    def delta(*names):
        values = [after.get(name, 0) - before.get(name, 0) for name in names]
        return next((value for value in values if value > 0), None)
    prompt_tokens = delta(
        "vllm:request_prefill_kv_computed_tokens_sum",
        "vllm:request_prompt_tokens_sum",
        "vllm:prompt_tokens_total",
    )
    prompt_seconds = delta("vllm:request_prefill_time_seconds_sum")
    decode_tokens = delta("vllm:request_generation_tokens_sum", "vllm:generation_tokens_total")
    decode_seconds = delta("vllm:request_decode_time_seconds_sum", "vllm:inter_token_latency_seconds_sum")
    result = {}
    # A prompt-token counter alone is not a prefill clock. Only expose this
    # field when vLLM also exports its request-prefill phase duration.
    if prompt_tokens and prompt_seconds:
        result["server_prefill_tok_s"] = round(prompt_tokens / prompt_seconds, 3)
    if decode_tokens and decode_seconds:
        result["server_decode_tok_s"] = round(decode_tokens / decode_seconds, 3)
    ttft_sum = delta("vllm:time_to_first_token_seconds_sum")
    ttft_count = delta("vllm:time_to_first_token_seconds_count")
    if ttft_sum and ttft_count:
        result["server_ttft_seconds"] = round(ttft_sum / ttft_count, 3)
    return result

def maybe_model_info(base_url, model_id, api_key=None):
    try:
        models = get_json(f"{base_url.rstrip('/')}/models", 30, api_key)
    except Exception:
        return None
    for item in models.get("data", []):
        if item.get("id") == model_id:
            return item
    return None

def infer_family(model_id):
    lowered = (model_id or "").lower()
    if "qwen3.8" in lowered:
        return "Qwen3.8"
    if "qwen3.6" in lowered:
        return "Qwen3.6"
    if "qwen3.5" in lowered:
        return "Qwen3.5"
    if "gemma4" in lowered or "gemma 4" in lowered:
        return "Gemma4"
    return "unknown"


def infer_hardware_lane(gpu_count, gpu_model):
    model = (gpu_model or "").lower()
    is_5060ti = "5060" in model and "ti" in model
    if is_5060ti and gpu_count == 1:
        return "1x5060ti"
    if is_5060ti and gpu_count == 2:
        return "2x5060ti"
    if is_5060ti and gpu_count and gpu_count >= 3:
        return "multi-5060ti"
    if is_5060ti:
        return "mixed-5060ti-cuda"
    return "other-cuda"


def infer_quant(status):
    if not status:
        return "unknown"
    args = status.get("args") or []
    model_path = ""
    for index, value in enumerate(args):
        if value in {"--model", "-m"} and index + 1 < len(args):
            model_path = args[index + 1]
            break
    basename = model_path.rsplit("/", 1)[-1]
    matches = re.findall(r"(UD-[A-Z0-9_]+|IQ[0-9]_[A-Z0-9_]+|Q[0-9]_[A-Z0-9_]+|Q[0-9]_K_[A-Z]+)", basename)
    return matches[-1] if matches else "unknown"


def arg_after(args, *names):
    for index, value in enumerate(args):
        if value in names and index + 1 < len(args):
            return args[index + 1]
    return None


def positive_int_or_none(value):
    if value is None:
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def status_arg(status, *names):
    return arg_after((status or {}).get("args") or [], *names)


def status_reasoning_enabled(status):
    return status_arg(status, "--reasoning") == "on"


def status_reasoning_budget(status):
    return positive_int_or_none(status_arg(status, "--reasoning-budget"))


def request_max_tokens(prompt_config, status, args):
    target_tokens = prompt_config["max_tokens"]
    reasoning_budget = args.reasoning_budget or status_reasoning_budget(status)
    thinking_enabled = not args.no_thinking and (args.thinking == "on" or status_reasoning_enabled(status))
    if thinking_enabled and reasoning_budget:
        return target_tokens + reasoning_budget
    return target_tokens


def sanitize_public_text(value):
    if not isinstance(value, str):
        return value
    cleaned = value
    cleaned = re.sub(r"(Bearer )([A-Za-z0-9._-]{10,})", r"\1<redacted>", cleaned)
    cleaned = re.sub(r"(hf_|sk-)([A-Za-z0-9._-]{10,})", r"\1<redacted>", cleaned)
    cleaned = re.sub(r"\b(192\.168|10\.[0-9]{1,3}|172\.(1[6-9]|2[0-9]|3[0-1]))(\.[0-9]{1,3}){2}\b", "<private-ip>", cleaned)
    cleaned = re.sub(r"https?://[^\s/]+", "https://<redacted-host>", cleaned)
    cleaned = re.sub(r"/(home|Users|root)/[^\s'\\\"]+", "/<redacted-path>", cleaned)
    return cleaned


def write_report(path, result_json_path, results):
    lines = [
        "# club-5060ti result report",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Submission Checklist",
        "",
        "- Removed private IPs, hostnames, tokens, and personal paths from launch/config text.",
        "- Included exact runtime, model, quant, context, KV cache, and caveats.",
        "- Kept benchmark JSON attached for schema validation.",
        "",
        "## Result JSON",
        "",
        f"- File: {Path(result_json_path).name}",
        f"- Result count: {len(results)}",
        "",
        "## Benchmark Summary",
        "",
        "| model | prompt_set | generated_tokens | decode_tok_s | end_to_end_tok_s | wall_seconds |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]

    for item in results:
        model_id = item.get("model", {}).get("id", "unknown")
        prompt_set = item.get("benchmark", {}).get("prompt_set", "unknown")
        generated_tokens = item.get("benchmark", {}).get("generated_tokens", "")
        metrics = item.get("metrics", {})
        decode = metrics.get("decode_tok_s", "")
        end_to_end = metrics.get("end_to_end_tok_s", "")
        wall_seconds = metrics.get("wall_seconds", "")
        lines.append(
            f"| {model_id} | {prompt_set} | {generated_tokens} | {decode} | {end_to_end} | {wall_seconds} |"
        )

    lines.extend(
        [
            "",
            "## Hardware",
            "",
            "- Hardware lane:",
            "- GPU(s):",
            "- VRAM per GPU:",
            "- Driver:",
            "- CPU:",
            "- Host RAM:",
            "- Inference/container RAM:",
            "- Motherboard/system:",
            "- PCIe layout/link width:",
            "- OS/container:",
            "",
            "## Runtime Settings",
            "",
            "- Runtime/version/commit:",
            "- Launch command/config (sanitized):",
            "- Context length:",
            "- KV cache:",
            "- Tensor parallel / tensor split:",
            "- MTP/speculative settings:",
            "- Thinking/reasoning enabled:",
            "- Notes/warnings:",
            "",
        ]
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def build_result(args, model_id, model_info, status, prompt_set, run_index, response, elapsed, client_metrics=None, run_nonce=""):
    model_info = model_info or {}
    usage = response.get("usage") or {}
    timings = response.get("timings") or {}
    client_metrics = client_metrics or {}
    status_args = (status or {}).get("args") or []
    server_max_context = positive_int_or_none(model_info.get("max_model_len"))
    prompt_tokens = usage.get("prompt_tokens")
    completion_tokens = usage.get("completion_tokens")
    predicted_per_second = timings.get("predicted_per_second")
    prompt_per_second = timings.get("prompt_per_second")
    draft_n_generated = positive_int_or_none(timings.get("draft_n"))
    draft_n_accepted = positive_int_or_none(timings.get("draft_n_accepted"))
    acceptance_rate = None
    if draft_n_generated and draft_n_accepted is not None and draft_n_generated > 0:
        acceptance_rate = round(draft_n_accepted / draft_n_generated, 5)
    context_tokens = positive_int_or_none(arg_after(status_args, "--ctx-size", "-c") or args.context_tokens)
    batch_size = positive_int_or_none(arg_after(status_args, "--batch-size", "-b") or args.batch_size)
    ubatch_size = positive_int_or_none(arg_after(status_args, "--ubatch-size", "-ub") or args.ubatch_size)
    draft_n = positive_int_or_none(arg_after(status_args, "--spec-draft-n-max") or args.draft_n)
    spec_p_min = arg_after(status_args, "--spec-draft-p-min") or args.spec_draft_p_min
    split_mode = arg_after(status_args, "--split-mode", "-sm") or args.split_mode

    speculation_notes = args.speculation_notes
    if spec_p_min:
        speculation_notes = f"{speculation_notes} p-min={spec_p_min}".strip()

    quant = args.quant or infer_quant(status)
    benchmark_notes = args.benchmark_notes
    if prompt_set == "long-retrieval" and completion_tokens is not None and completion_tokens < 32:
        benchmark_notes = f"{benchmark_notes} short-answer fit check; sustained decode not measured".strip()
    result_id = "-".join(
        [
            slugify(args.run_id),
            slugify(model_id),
            slugify(prompt_set),
            str(run_index + 1),
        ]
    )

    return strip_nones({
        "schema_version": "1.0",
        "id": result_id,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "source": {
            "type": args.source_type,
            "label": args.source_label,
            "notes": "Generated by scripts/run_openai_bench.py",
        },
        "promotion_level": "benchmark",
        "tier": args.tier,
        "hardware": {
            "lane": args.hardware_lane or infer_hardware_lane(args.gpu_count, args.gpu_model),
            "gpu_count": args.gpu_count,
            "gpu_model": args.gpu_model,
            "vram_per_gpu_gb": args.vram_per_gpu_gb,
            "driver": args.driver,
            "cpu": args.cpu,
            "host_ram_gb": args.host_ram_gb,
            "inference_ram_gb": args.inference_ram_gb,
            "pcie": args.pcie,
            "notes": args.hardware_notes,
        },
        "runtime": {
            "engine": args.engine,
            "version": args.runtime_version,
            "commit": args.runtime_commit,
            "build": args.runtime_build,
            "notes": args.runtime_notes,
        },
        "model": {
            "id": model_id,
            "server_max_context_tokens": server_max_context,
            "family": args.family or infer_family(model_id),
            "architecture": args.architecture,
            "parameter_class": args.parameter_class,
            "quant": quant,
            "source": args.model_source,
            "notes": args.model_notes,
        },
        "serving": {
            "route": "server",
            "context_tokens": context_tokens,
            "server_max_model_len": server_max_context,
            "batch_size": batch_size,
            "ubatch_size": ubatch_size,
            "kv_cache_k": arg_after(status_args, "--cache-type-k") or args.kv_cache_k,
            "kv_cache_v": arg_after(status_args, "--cache-type-v") or args.kv_cache_v,
            "split_mode": split_mode,
            "tensor_parallel": arg_after(status_args, "--tensor-split", "-ts") or args.tensor_parallel,
            "speculation": {
                "type": arg_after(status_args, "--spec-type") or args.speculation_type,
                "draft_n": draft_n,
                "acceptance_rate": acceptance_rate,
                "notes": speculation_notes,
            },
            "thinking": args.thinking,
            "reasoning_budget": args.reasoning_budget or status_reasoning_budget(status),
            "notes": args.serving_notes,
        },
        "benchmark": {
            "prompt_set": prompt_set,
            "configured_context_tokens": context_tokens,
            "actual_prompt_tokens": prompt_tokens,
            "generated_tokens": completion_tokens,
            "runs": 1,
            "warmups": args.warmups,
            "stream": args.stream,
            "preset_id": args.preset,
            "cache_policy": args.cache_policy,
            "run_nonce": run_nonce,
            "server_max_context_tokens": server_max_context,
            "prompt_calibration": {
                "method": "server-reported usage.prompt_tokens",
                "target_tokens": args.target_prompt_tokens or None,
                "tolerance_tokens": args.prompt_token_tolerance,
                "filler_lines": args.long_retrieval_filler_lines if prompt_set == "long-retrieval" else None,
            },
            "tool_call_validated": prompt_set == "tool-call",
            "notes": benchmark_notes,
        },
        "metrics": {
            "prompt_tok_s": prompt_per_second,
            "decode_tok_s": predicted_per_second,
            "end_to_end_tok_s": round(completion_tokens / elapsed, 3) if completion_tokens else None,
            "wall_seconds": round(elapsed, 3),
            "client_ttft_seconds": client_metrics.get("client_ttft_seconds"),
            "client_decode_tok_s": client_metrics.get("client_decode_tok_s"),
            "client_end_to_end_tok_s": client_metrics.get("client_end_to_end_tok_s"),
            "server_prefill_tok_s": client_metrics.get("server_prefill_tok_s"),
            "server_decode_tok_s": client_metrics.get("server_decode_tok_s"),
            "server_ttft_seconds": client_metrics.get("server_ttft_seconds"),
        },
        "caveats": args.caveat,
    })


def strip_nones(value):
    if isinstance(value, dict):
        return {key: strip_nones(item) for key, item in value.items() if item is not None and item != ""}
    if isinstance(value, list):
        return [strip_nones(item) for item in value if item is not None and item != ""]
    return value


def validate_tool_call_response(response):
    try:
        calls = response["choices"][0]["message"]["tool_calls"]
        call = next(call for call in calls if (call.get("function") or {}).get("name") == TOOL_NAME)
        arguments = json.loads((call.get("function") or {}).get("arguments") or "{}")
    except (KeyError, IndexError, StopIteration, TypeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"tool-call contract failed: expected {TOOL_NAME} with JSON arguments") from exc
    if arguments.get("note") != "vLLM tool-call contract passed" or arguments.get("severity") != "info":
        raise RuntimeError("tool-call contract failed: arguments did not match deterministic expected values")
    return True


def run_prompt(base_url, model_id, prompt_set, prompt_config, args, status, run_nonce=""):
    text = prompt_config["text"]
    if prompt_set == "long-retrieval" and args.cache_policy == "no-reuse":
        text = f"Benchmark run nonce: {run_nonce}\n\n{text}"
    payload = {
        "model": model_id,
        "messages": [{"role": "user", "content": text}],
        "temperature": args.temperature,
        "max_tokens": request_max_tokens(prompt_config, status, args),
        "stream": False,
    }
    if prompt_config.get("tools"):
        payload["tools"] = prompt_config["tools"]
        payload["tool_choice"] = prompt_config["tool_choice"]
    if args.no_thinking:
        payload["chat_template_kwargs"] = {"enable_thinking": False}
    if args.cache_policy == "no-reuse":
        payload["cache_prompt"] = False
    endpoint = f"{base_url.rstrip('/')}/chat/completions"
    request_headers = {"x-benchmark-cache-policy": args.cache_policy}
    if run_nonce:
        request_headers["x-benchmark-run-nonce"] = run_nonce
    if args.stream:
        response, elapsed, metrics = post_stream_json(endpoint, payload, args.timeout, args.api_key, args.metrics_url, request_headers)
    else:
        started = time.monotonic()
        response = post_json(endpoint, payload, args.timeout, args.api_key, request_headers)
        elapsed = time.monotonic() - started
        metrics = {}
    if prompt_set == "tool-call":
        validate_tool_call_response(response)
    usage = response.get("usage") or {}
    actual_tokens = positive_int_or_none(usage.get("prompt_tokens"))
    if prompt_set == "long-retrieval" and args.min_prompt_tokens and (actual_tokens is None or actual_tokens < args.min_prompt_tokens):
        raise RuntimeError(f"long-retrieval prompt calibration failed: got {actual_tokens}, need >= {args.min_prompt_tokens}")
    if args.target_prompt_tokens:
        if actual_tokens is None:
            raise RuntimeError("prompt calibration failed: server did not return usage.prompt_tokens")
        if abs(actual_tokens - args.target_prompt_tokens) > args.prompt_token_tolerance:
            raise RuntimeError(f"prompt calibration outside bound: got {actual_tokens}, target {args.target_prompt_tokens} +/- {args.prompt_token_tolerance}")
    return response, elapsed, metrics

def main():
    parser = argparse.ArgumentParser(description="Run protocol-shaped OpenAI-compatible benchmark prompts.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8080/v1")
    parser.add_argument("--api-key", default=os.environ.get("LLAMA_API_KEY", ""))
    parser.add_argument("--model", action="append", required=True)
    parser.add_argument("--prompt-set", action="append", choices=sorted(PROMPT_SET_CHOICES), default=None)
    parser.add_argument("--no-cache-prompt", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--cache-policy", choices=CACHE_POLICIES, default="server-default", help="no-reuse adds a per-request nonce and compatibility cache_prompt=false.")
    parser.add_argument("--metrics-url", default="", help="Optional vLLM Prometheus endpoint for server prefill/decode deltas.")
    parser.add_argument("--preset", default="", help="Canonical preset id to link into the result metadata.")
    parser.add_argument("--target-prompt-tokens", type=int, default=0, help="Require server usage.prompt_tokens within the tolerance.")
    parser.add_argument("--prompt-token-tolerance", type=int, default=256)
    parser.add_argument("--min-prompt-tokens", type=int, default=0, help="Minimum server-reported prompt tokens for long-retrieval calibration.")
    parser.add_argument(
        "--long-retrieval-filler-lines",
        type=int,
        default=900,
        help="Number of filler lines used in the long-retrieval prompt body (default: 900).",
    )
    parser.add_argument(
        "--long-retrieval-max-tokens",
        type=int,
        default=96,
        help="Output token cap for the long-retrieval prompt set (default: 96).",
    )
    parser.add_argument(
        "--custom-prompt-text",
        default="",
        help="Literal prompt text for prompt-set=custom.",
    )
    parser.add_argument(
        "--custom-prompt-file",
        default="",
        help="Path to UTF-8 prompt text file for prompt-set=custom.",
    )
    parser.add_argument(
        "--custom-max-tokens",
        type=int,
        default=512,
        help="Output token cap for prompt-set=custom (default: 512).",
    )
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--warmups", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--stream", action="store_true", help="Measure client-side TTFT and decode from OpenAI-compatible SSE; required for vLLM timing.")
    parser.add_argument("--no-thinking", action="store_true")
    parser.add_argument("--output", required=True)
    parser.add_argument("--report-output", default="", help="Optional markdown report output path")
    parser.add_argument("--run-id", default=datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S"))
    parser.add_argument("--source-type", default="community", choices=sorted(SOURCE_TYPES))
    parser.add_argument("--source-label", default="community-5060ti")
    parser.add_argument(
        "--tier",
        default="capable",
        choices=sorted(TIERS),
        help="Public explorer tier. Use capable for new measured results; recommended is a maintainer decision.",
    )
    parser.add_argument("--gpu-count", type=int, default=1)
    parser.add_argument("--hardware-lane", default="", choices=[""] + sorted(HARDWARE_LANES))
    parser.add_argument("--gpu-model", default="RTX 5060 Ti")
    parser.add_argument("--vram-per-gpu-gb", type=float, default=16)
    parser.add_argument("--driver", default="")
    parser.add_argument("--cpu", default="")
    parser.add_argument("--host-ram-gb", type=float, default=None)
    parser.add_argument("--inference-ram-gb", type=float, default=None)
    parser.add_argument("--pcie", default="")
    parser.add_argument("--hardware-notes", default="")
    parser.add_argument("--engine", default="llama.cpp", choices=["llama.cpp", "ik_llama.cpp", "BeeLlama", "vLLM", "SGLang", "other"])
    parser.add_argument("--runtime-version", default="")
    parser.add_argument("--runtime-commit", default="")
    parser.add_argument("--runtime-build", default="")
    parser.add_argument("--runtime-notes", default="")
    parser.add_argument("--family", default="")
    parser.add_argument("--architecture", default="unknown", choices=["dense", "moe", "hybrid", "unknown"])
    parser.add_argument("--parameter-class", default="")
    parser.add_argument("--quant", default="")
    parser.add_argument("--model-source", default="")
    parser.add_argument("--model-notes", default="")
    parser.add_argument("--context-tokens", type=int, default=8192)
    parser.add_argument("--batch-size", type=int, default=0)
    parser.add_argument("--ubatch-size", type=int, default=0)
    parser.add_argument("--kv-cache-k", default="unknown")
    parser.add_argument("--kv-cache-v", default="unknown")
    parser.add_argument("--split-mode", default="", choices=["", "none", "layer", "row", "tensor"])
    parser.add_argument("--tensor-parallel", default="")
    parser.add_argument("--speculation-type", default="none")
    parser.add_argument("--draft-n", type=int, default=0)
    parser.add_argument("--spec-draft-p-min", default="")
    parser.add_argument("--speculation-notes", default="")
    parser.add_argument("--thinking", default="unknown", choices=["on", "off", "unknown"])
    parser.add_argument("--reasoning-budget", type=int, default=0, help="Add this token budget to prompt-set output caps when thinking is on")
    parser.add_argument("--serving-notes", default="")
    parser.add_argument("--benchmark-notes", default="")
    parser.add_argument("--caveat", action="append", default=[])
    args = parser.parse_args()

    if args.source_type == "community":
        for name in [
            "source_label",
            "hardware_notes",
            "runtime_notes",
            "model_notes",
            "serving_notes",
            "benchmark_notes",
        ]:
            setattr(args, name, sanitize_public_text(getattr(args, name)))
        args.caveat = [sanitize_public_text(item) for item in args.caveat]

    if args.long_retrieval_filler_lines < 1:
        raise SystemExit("--long-retrieval-filler-lines must be >= 1")
    if args.long_retrieval_max_tokens < 1:
        raise SystemExit("--long-retrieval-max-tokens must be >= 1")
    if args.custom_max_tokens < 1:
        raise SystemExit("--custom-max-tokens must be >= 1")

    prompts = build_prompts(
        long_retrieval_filler_lines=args.long_retrieval_filler_lines,
        long_retrieval_max_tokens=args.long_retrieval_max_tokens,
    )
    custom_prompt_text = args.custom_prompt_text
    if args.custom_prompt_file:
        custom_prompt_text = Path(args.custom_prompt_file).read_text(encoding="utf-8")
    if custom_prompt_text:
        prompts["custom"] = {
            "max_tokens": args.custom_max_tokens,
            "text": custom_prompt_text,
        }
    prompt_sets = args.prompt_set or ["short-chat", "code-generate", "agent-tool"]
    if "custom" in prompt_sets and "custom" not in prompts:
        raise SystemExit("prompt-set=custom requires --custom-prompt-text or --custom-prompt-file")
    results = []

    if args.no_cache_prompt:
        args.cache_policy = "no-reuse"
    for model_id in args.model:
        model_info = maybe_model_info(args.base_url, model_id, args.api_key)
        status = (model_info or {}).get("status")
        server_max_context = positive_int_or_none((model_info or {}).get("max_model_len"))
        if server_max_context and args.context_tokens > server_max_context:
            raise SystemExit(f"requested context {args.context_tokens} exceeds server max_model_len {server_max_context}")
        for prompt_set in prompt_sets:
            prompt_config = prompts[prompt_set]
            for warmup_index in range(args.warmups):
                nonce = secrets.token_hex(8) if prompt_set == "long-retrieval" and args.cache_policy == "no-reuse" else ""
                run_prompt(args.base_url, model_id, prompt_set, prompt_config, args, status, nonce)
            for run_index in range(args.runs):
                nonce = secrets.token_hex(8) if prompt_set == "long-retrieval" and args.cache_policy == "no-reuse" else ""
                response, elapsed, client_metrics = run_prompt(args.base_url, model_id, prompt_set, prompt_config, args, status, nonce)
                results.append(build_result(args, model_id, model_info, status, prompt_set, run_index, response, elapsed, client_metrics, nonce))

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"results": results}, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(results)} result(s) to {output}")
    if args.report_output:
        report_output = Path(args.report_output)
        write_report(report_output, output, results)
        print(f"wrote report template to {report_output}")


if __name__ == "__main__":
    raise SystemExit(main())
