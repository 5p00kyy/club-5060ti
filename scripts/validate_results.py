#!/usr/bin/env python3
import argparse
import json
import re
import sys
from pathlib import Path


REQUIRED_TOP = {
    "schema_version",
    "id",
    "timestamp_utc",
    "source",
    "promotion_level",
    "tier",
    "hardware",
    "runtime",
    "model",
    "serving",
    "benchmark",
    "metrics",
}

PROMOTION_LEVELS = {"exploratory", "recipe", "benchmark", "verified", "deprecated"}
TIERS = {"recommended", "capable", "experimental"}
SOURCE_TYPES = {"seed", "community", "imported", "external"}
ENGINES = {"llama.cpp", "ik_llama.cpp", "BeeLlama", "vLLM", "SGLang", "other"}
PROMPT_SETS = {
    "short-chat",
    "code-generate",
    "agent-tool",
    "long-retrieval",
    "vision-smoke",
    "legacy",
    "custom",
}
HARDWARE_LANES = {"1x5060ti", "2x5060ti", "multi-5060ti", "mixed-5060ti-cuda", "other-cuda", "unknown"}

PRIVATE_IPV4_RE = re.compile(r"\b(192\.168|10\.[0-9]{1,3}|172\.(1[6-9]|2[0-9]|3[0-1]))(\.[0-9]{1,3}){2}\b")
TOKEN_RE = re.compile(r"(Bearer\s+[A-Za-z0-9._-]{10,}|hf_[A-Za-z0-9]{10,}|sk-[A-Za-z0-9]{10,})")
PRIVATE_PATH_RE = re.compile(r"/(home|Users|root)/[^\s'\"\\]+")


def find_sensitive_strings(value, path):
    findings = []
    if isinstance(value, dict):
        for key, item in value.items():
            findings.extend(find_sensitive_strings(item, f"{path}.{key}" if path else str(key)))
        return findings
    if isinstance(value, list):
        for index, item in enumerate(value):
            findings.extend(find_sensitive_strings(item, f"{path}[{index}]"))
        return findings
    if not isinstance(value, str):
        return findings
    if PRIVATE_IPV4_RE.search(value):
        findings.append(f"{path}: contains private IPv4 address")
    if TOKEN_RE.search(value):
        findings.append(f"{path}: contains token-like secret")
    if PRIVATE_PATH_RE.search(value):
        findings.append(f"{path}: contains personal absolute path")
    return findings


def load_results(path):
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "results" in data:
        results = data["results"]
        if not isinstance(results, list):
            raise ValueError(f"{path}: results must be a list")
        return results
    if isinstance(data, dict):
        return [data]
    raise ValueError(f"{path}: expected object, list, or object with results")


def require(condition, errors, message):
    if not condition:
        errors.append(message)


def validate_result(result, label, allow_private=False):
    errors = []
    require(isinstance(result, dict), errors, f"{label}: result must be an object")
    if errors:
        return errors

    missing = sorted(REQUIRED_TOP - set(result))
    require(not missing, errors, f"{label}: missing required fields: {', '.join(missing)}")
    require(result.get("schema_version") == "1.0", errors, f"{label}: schema_version must be 1.0")
    require(result.get("promotion_level") in PROMOTION_LEVELS, errors, f"{label}: invalid promotion_level")
    require(result.get("tier") in TIERS, errors, f"{label}: tier must be recommended, capable, or experimental")

    source = result.get("source") or {}
    require(isinstance(source, dict), errors, f"{label}: source must be an object")
    require(source.get("type") in SOURCE_TYPES, errors, f"{label}: source.type is invalid")
    require(bool(source.get("type")), errors, f"{label}: source.type is required")
    require(bool(source.get("label")), errors, f"{label}: source.label is required")

    hardware = result.get("hardware") or {}
    require(isinstance(hardware, dict), errors, f"{label}: hardware must be an object")
    if hardware.get("lane") is not None:
        require(hardware.get("lane") in HARDWARE_LANES, errors, f"{label}: hardware.lane is invalid")
    require(isinstance(hardware.get("gpu_count"), int), errors, f"{label}: hardware.gpu_count must be an integer")
    require(bool(hardware.get("gpu_model")), errors, f"{label}: hardware.gpu_model is required")
    require(isinstance(hardware.get("vram_per_gpu_gb"), (int, float)), errors, f"{label}: hardware.vram_per_gpu_gb must be numeric")

    runtime = result.get("runtime") or {}
    require(runtime.get("engine") in ENGINES, errors, f"{label}: runtime.engine is invalid")

    model = result.get("model") or {}
    require(bool(model.get("id")), errors, f"{label}: model.id is required")
    require(bool(model.get("family")), errors, f"{label}: model.family is required")
    require(bool(model.get("quant")), errors, f"{label}: model.quant is required")

    benchmark = result.get("benchmark") or {}
    require(benchmark.get("prompt_set") in PROMPT_SETS, errors, f"{label}: benchmark.prompt_set is invalid")

    serving = result.get("serving") or {}
    for field in ("context_tokens", "batch_size", "ubatch_size"):
        if field in serving:
            require(isinstance(serving[field], int), errors, f"{label}: serving.{field} must be an integer")
            require(serving[field] > 0, errors, f"{label}: serving.{field} must be greater than 0")

    metrics = result.get("metrics") or {}
    metric_names = {"prompt_tok_s", "decode_tok_s", "end_to_end_tok_s", "wall_seconds", "ttft_seconds", "load_seconds", "quality_score"}
    for name in metric_names:
        if name in metrics and metrics[name] is not None:
            require(isinstance(metrics[name], (int, float)), errors, f"{label}: metrics.{name} must be numeric")

    if not allow_private:
        for finding in find_sensitive_strings(result, ""):
            errors.append(f"{label}: {finding}")

    return errors


def has_metric(result, *names):
    metrics = result.get("metrics") or {}
    return any(metrics.get(name) is not None for name in names)


def combined_notes(result):
    parts = []
    for path in (
        ("benchmark", "notes"),
        ("serving", "notes"),
        ("runtime", "notes"),
        ("model", "notes"),
    ):
        value = result
        for key in path:
            value = (value or {}).get(key)
        if value:
            parts.append(str(value))
    parts.extend(str(item) for item in result.get("caveats", []) if item)
    return " ".join(parts).lower()


def setup_group_key(result):
    serving = result.get("serving") or {}
    benchmark = result.get("benchmark") or {}
    speculation = serving.get("speculation") or {}
    return (
        (result.get("model") or {}).get("id"),
        (result.get("model") or {}).get("family"),
        (result.get("model") or {}).get("quant"),
        (result.get("runtime") or {}).get("engine"),
        (result.get("runtime") or {}).get("version"),
        (result.get("runtime") or {}).get("commit"),
        (result.get("hardware") or {}).get("gpu_count"),
        (result.get("hardware") or {}).get("gpu_model"),
        (result.get("hardware") or {}).get("driver"),
        (result.get("hardware") or {}).get("pcie"),
        serving.get("context_tokens"),
        serving.get("batch_size"),
        serving.get("ubatch_size"),
        serving.get("kv_cache_k"),
        serving.get("kv_cache_v"),
        serving.get("tensor_parallel"),
        serving.get("split_mode"),
        serving.get("gpu_layers"),
        speculation.get("type"),
        speculation.get("draft_n"),
        serving.get("thinking"),
        benchmark.get("prompt_set"),
        benchmark.get("configured_context_tokens"),
        benchmark.get("actual_prompt_tokens"),
        benchmark.get("generated_tokens"),
        benchmark.get("warmups"),
        benchmark.get("stream"),
        result.get("promotion_level"),
        (result.get("source") or {}).get("type"),
        (result.get("source") or {}).get("label"),
    )


def validate_dataset(results):
    errors = []
    seen_ids = {}
    groups = {}

    for label, result in results:
        result_id = result.get("id")
        if result_id:
            if result_id in seen_ids:
                errors.append(f"{label}: duplicate id also appears at {seen_ids[result_id]}: {result_id}")
            else:
                seen_ids[result_id] = label

        level = result.get("promotion_level")
        tier = result.get("tier")
        benchmark = result.get("benchmark") or {}
        if level == "deprecated" and tier != "experimental":
            errors.append(f"{label}: deprecated rows must use the experimental tier")
        prompt_set = benchmark.get("prompt_set")
        notes = combined_notes(result)

        if level in {"benchmark", "verified"} and prompt_set != "legacy":
            if not has_metric(result, "decode_tok_s", "prompt_tok_s", "end_to_end_tok_s"):
                errors.append(f"{label}: benchmark/verified rows need comparable speed metrics")

        if level == "deprecated" and prompt_set == "legacy" and not has_metric(result, "decode_tok_s", "prompt_tok_s", "end_to_end_tok_s"):
            if "fit-only" not in notes:
                errors.append(f"{label}: archived legacy row without speed metrics must be labeled fit-only")

        generated = benchmark.get("generated_tokens")
        if prompt_set == "long-retrieval" and isinstance(generated, int) and generated < 32:
            if "short-answer" not in notes or "sustained decode" not in notes:
                errors.append(f"{label}: long-retrieval rows below 32 generated tokens must be labeled as short-answer fit checks")

        groups.setdefault(setup_group_key(result), []).append(result_id or label)

    # Repeated benchmark runs are allowed, but broad accidental duplicates should
    # still be visible to maintainers during review.
    for ids in groups.values():
        if len(ids) > 8:
            errors.append(f"setup group has an unusually large repeat count ({len(ids)}): {', '.join(ids[:5])}...")

    return errors


def main():
    parser = argparse.ArgumentParser(description="Validate club-5060ti result JSON files.")
    parser.add_argument("paths", nargs="+", help="JSON files or directories under data/results")
    parser.add_argument("--allow-private", action="store_true", help="Skip private-data lint checks")
    args = parser.parse_args()

    files = []
    for raw in args.paths:
        path = Path(raw)
        if path.is_dir():
            files.extend(sorted(path.glob("*.json")))
        else:
            files.append(path)

    all_errors = []
    labeled_results = []
    count = 0
    for path in files:
        try:
            results = load_results(path)
        except Exception as exc:
            all_errors.append(str(exc))
            continue
        for index, result in enumerate(results):
            count += 1
            label = f"{path}:{index}"
            if isinstance(result, dict):
                labeled_results.append((label, result))
            all_errors.extend(validate_result(result, label, allow_private=args.allow_private))

    all_errors.extend(validate_dataset(labeled_results))

    if all_errors:
        for error in all_errors:
            print(error, file=sys.stderr)
        return 1

    print(f"validated {count} result(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
