#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def load_result_file(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "results" in data:
        return data["results"]
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return [data]
    return []


def positive_number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
        return None
    return float(value)


def display_metrics(item):
    metrics = item.get("metrics") or {}
    benchmark = item.get("benchmark") or {}
    display = {}

    for field, source in (
        ("decode_tok_s", "reported"),
        ("client_decode_tok_s", "client"),
        ("server_decode_tok_s", "server"),
    ):
        value = positive_number(metrics.get(field))
        if value is not None:
            display["decode_tok_s"] = value
            display["decode_source"] = source
            break

    for field, source in (
        ("prompt_tok_s", "reported"),
        ("server_prefill_tok_s", "server"),
    ):
        value = positive_number(metrics.get(field))
        if value is not None:
            display["prompt_tok_s"] = value
            display["prompt_source"] = source
            break

    if "prompt_tok_s" not in display and benchmark.get("prompt_set") == "long-retrieval" and benchmark.get("cache_policy") == "no-reuse":
        prompt_tokens = positive_number(benchmark.get("actual_prompt_tokens"))
        client_ttft = positive_number(metrics.get("client_ttft_seconds"))
        if prompt_tokens is not None and client_ttft is not None:
            display["prompt_tok_s"] = round(prompt_tokens / client_ttft, 3)
            display["prompt_source"] = "client-ttft-derived"

    return display


def repeat_prompt_key(item):
    benchmark = item.get("benchmark") or {}
    calibration = benchmark.get("prompt_calibration") or {}
    target_tokens = calibration.get("target_tokens")
    filler_lines = calibration.get("filler_lines")
    if not target_tokens and not filler_lines:
        return None
    return "|".join(
        str(value or "")
        for value in (
            "calibrated",
            calibration.get("method"),
            target_tokens,
            calibration.get("tolerance_tokens"),
            filler_lines,
        )
    )


def prepare_site_item(item, path):
    prepared = dict(item)
    prepared["_source_file"] = str(path)
    metrics = display_metrics(prepared)
    if any(value != "reported" for key, value in metrics.items() if key.endswith("_source")):
        prepared["_display_metrics"] = metrics
    prompt_key = repeat_prompt_key(prepared)
    if prompt_key is not None:
        prepared["_repeat_prompt_key"] = prompt_key
    return prepared


def main():
    parser = argparse.ArgumentParser(description="Build static site data from data/results/*.json.")
    parser.add_argument("--results-dir", default="data/results")
    parser.add_argument("--output", default="site/data/results.json")
    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    results = []
    for path in sorted(results_dir.glob("*.json")):
        for item in load_result_file(path):
            results.append(prepare_site_item(item, path))

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"results": results}, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(results)} result(s) to {output}")


if __name__ == "__main__":
    raise SystemExit(main())
