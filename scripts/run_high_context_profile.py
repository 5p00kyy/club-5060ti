#!/usr/bin/env python3
"""Validate one already-loaded context tier with calibrated, uncached workloads.

Raw output defaults to .local/bench. This script does not restart services or
change serving flags: that would make a different preset, not a fit result.
"""
import argparse
import json
import math
import os
import secrets
import statistics
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

NEEDLE = "CLUB-5060TI-HIGH-CONTEXT-NEEDLE-48291"
FILLER = "Benchmark context filler. Preserve operational facts, configuration fields, and evidence boundaries.\n"


def request(url, payload, timeout, api_key):
    headers = {"content-type": "application/json"}
    if api_key:
        headers["authorization"] = f"Bearer {api_key}"
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode())


def get_json(url, timeout, api_key):
    headers = {"authorization": f"Bearer {api_key}"} if api_key else {}
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=timeout) as response:
        return json.loads(response.read().decode())


def arg_after(values, *names):
    for index, value in enumerate(values or []):
        if value in names and index + 1 < len(values):
            return values[index + 1]
    return None


def prompt(kind, lines, nonce):
    # Keep this at the start of the user message. llama.cpp can reuse a matching
    # longest common prefix even when a client asks to bypass prompt caching. A
    # unique leading nonce means timing measures this request's own prefill.
    prefix = "Benchmark request nonce: " + nonce + ". Do not repeat it.\n\n"
    if kind == "retrieval":
        suffix = "\nQuestion: reply with only the exact key."
        prefix += "Remember this exact key: " + NEEDLE + "\n\n"
    else:
        suffix = "\nWrite a detailed, practical guide to validating a local inference preset. Cover context fit, retrieval, sustained generation, caveats, and reproducibility."
        prefix += "Use the following local benchmark context as source material.\n\n"
    return prefix + FILLER * lines + suffix


def response_parts(response):
    """Keep final answer and reasoning separate for client-visible validation."""
    visible, reasoning = [], []
    for choice in response.get("choices") or []:
        message = choice.get("message") or {}
        content = message.get("content")
        if isinstance(content, str):
            visible.append(content)
        for field in ("reasoning_content", "reasoning"):
            value = message.get(field)
            if isinstance(value, str):
                reasoning.append(value)
    return "".join(visible), "".join(reasoning)


def call(args, kind, lines, output_tokens):
    nonce = secrets.token_hex(12)
    payload = {
        "model": args.model,
        "messages": [{"role": "user", "content": prompt(kind, lines, nonce)}],
        "temperature": 0,
        "max_tokens": output_tokens,
        "stream": False,
        "cache_prompt": False,
    }
    if args.disable_thinking:
        payload["chat_template_kwargs"] = {"enable_thinking": False}
    started = time.monotonic()
    try:
        response = request(args.base_url.rstrip("/") + "/chat/completions", payload, args.timeout, args.api_key)
    except Exception as exc:
        return {"kind": kind, "lines": lines, "passed": False, "error": str(exc)}
    usage, timings = response.get("usage") or {}, response.get("timings") or {}
    visible, reasoning = response_parts(response)
    completion = usage.get("completion_tokens") or 0
    passed = (visible.strip() == NEEDLE if kind == "retrieval" else
              (completion >= math.ceil(output_tokens * args.minimum_output_fraction) and
               len(visible.strip()) >= args.minimum_visible_output_characters))
    return {
        "kind": kind, "lines": lines, "request_nonce": nonce, "passed": passed,
        "actual_prompt_tokens": usage.get("prompt_tokens"), "generated_tokens": completion,
        "prompt_tok_s": timings.get("prompt_per_second"), "decode_tok_s": timings.get("predicted_per_second"),
        "draft_generated": timings.get("draft_n"), "draft_accepted": timings.get("draft_n_accepted"),
        "draft_acceptance_rate": (round(timings["draft_n_accepted"] / timings["draft_n"], 5)
                                  if isinstance(timings.get("draft_n"), (int, float)) and timings["draft_n"] > 0
                                  and isinstance(timings.get("draft_n_accepted"), (int, float)) else None),
        "wall_seconds": round(time.monotonic() - started, 3),
        "response": visible[:500], "reasoning_response": reasoning[:500],
        "visible_output_characters": len(visible.strip()), "reasoning_output_characters": len(reasoning.strip()),
        "failure": None if passed else ("retrieval final-answer mismatch" if kind == "retrieval" else "generation stopped before required visible output"),
    }


def calibrate(args, kind, target_tokens, output_tokens):
    """Estimate filler from real server token counts, then correct it if needed."""
    probe = call(args, kind, 32, output_tokens)
    observed = probe.get("actual_prompt_tokens")
    if not observed:
        return None, [probe]
    per_line = max(0.01, observed / 32)
    lines = max(1, math.ceil(target_tokens / per_line))
    attempts = [probe]
    for _ in range(args.max_calibration_attempts):
        measured = call(args, kind, lines, output_tokens)
        attempts.append(measured)
        actual = measured.get("actual_prompt_tokens")
        if not actual:
            # A too-large prompt may be rejected. Back off conservatively and retry.
            lines = max(1, math.floor(lines * 0.80))
            continue
        if actual >= target_tokens and actual <= args.context_tokens - output_tokens:
            return lines, attempts
        ratio = target_tokens / actual
        lines = max(1, math.ceil(lines * min(1.25, max(0.70, ratio))))
    return None, attempts


def median(values):
    values = [float(value) for value in values if isinstance(value, (int, float)) and value > 0]
    return round(statistics.median(values), 3) if values else None


def main():
    parser = argparse.ArgumentParser(description="Validate retrieval and sustained generation at one already-loaded context tier.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8080/v1")
    parser.add_argument("--api-key", default=os.environ.get("LLAMA_API_KEY", ""))
    parser.add_argument("--model", required=True)
    parser.add_argument("--preset", required=True)
    parser.add_argument("--context-tokens", required=True, type=int, help="Context tier to validate. The running server must provide at least this many effective tokens per request.")
    parser.add_argument("--profile", default="data/benchmark-profiles/high-context.json")
    parser.add_argument("--retrieval-repeats", type=int, default=None)
    parser.add_argument("--sustained-repeats", type=int, default=None)
    parser.add_argument("--retrieval-output-tokens", type=int, default=None)
    parser.add_argument("--sustained-output-tokens", type=int, default=None)
    parser.add_argument("--minimum-prompt-fraction", type=float, default=None)
    parser.add_argument("--minimum-output-fraction", type=float, default=None,
                        help="Required fraction of requested sustained output; defaults to the profile policy.")
    parser.add_argument("--minimum-visible-output-characters", type=int, default=None,
                        help="Minimum client-visible response size for sustained generation; reasoning alone does not qualify.")
    parser.add_argument("--disable-thinking", action="store_true", help="Send chat_template_kwargs.enable_thinking=false for a deterministic non-thinking preset route.")
    parser.add_argument("--minimum-decode-tok-s", type=float, default=None)
    parser.add_argument("--max-calibration-attempts", type=int, default=4)
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("--output", default="")
    args = parser.parse_args()
    profile = json.loads(Path(args.profile).read_text(encoding="utf-8"))
    fit = profile["fit"]
    args.retrieval_repeats = args.retrieval_repeats or fit["retrieval_repeats"]
    args.sustained_repeats = args.sustained_repeats or fit["sustained_repeats"]
    args.retrieval_output_tokens = args.retrieval_output_tokens or fit["retrieval_output_tokens"]
    args.sustained_output_tokens = args.sustained_output_tokens or fit["sustained_output_tokens"]
    args.minimum_prompt_fraction = args.minimum_prompt_fraction or fit["minimum_prompt_fraction"]
    args.minimum_decode_tok_s = args.minimum_decode_tok_s if args.minimum_decode_tok_s is not None else fit["minimum_decode_tok_s"]
    args.minimum_visible_output_characters = (args.minimum_visible_output_characters
                                               if args.minimum_visible_output_characters is not None
                                               else fit["minimum_visible_output_characters"])
    args.minimum_output_fraction = (args.minimum_output_fraction
                                    if args.minimum_output_fraction is not None
                                    else fit["minimum_output_fraction"])
    if not 0 < args.minimum_output_fraction <= 1:
        raise SystemExit("minimum output fraction must be in (0, 1]")
    calibration_margin = fit.get("calibration_margin_tokens", 0)
    if not isinstance(calibration_margin, int) or calibration_margin < 0:
        raise SystemExit("profile calibration_margin_tokens must be a non-negative integer")
    if args.context_tokens < 1:
        raise SystemExit("--context-tokens must be positive")

    try:
        models = get_json(args.base_url.rstrip("/") + "/models", args.timeout, args.api_key).get("data", [])
    except Exception as exc:
        raise SystemExit(f"could not read /models: {exc}")
    active = next((item.get("status") or {} for item in models if item.get("id") == args.model), None)
    if active is None:
        raise SystemExit(f"model {args.model!r} is not listed by /models")
    reported_context = arg_after(active.get("args"), "--ctx-size", "-c")
    reported_parallel = arg_after(active.get("args"), "--parallel", "-np") or "1"
    try:
        reported_total = int(reported_context) if reported_context else None
        parallel = int(reported_parallel)
    except ValueError:
        raise SystemExit("server reported an invalid ctx-size or parallel value")
    if parallel < 1:
        raise SystemExit("server reported parallel < 1")
    effective_context = reported_total // parallel if reported_total else None
    if effective_context and effective_context < args.context_tokens:
        raise SystemExit(f"server reports ctx-size {reported_total} with parallel {parallel}, giving only {effective_context} effective tokens per request, below requested tier {args.context_tokens}")

    targets = {
        "retrieval": min(int(args.context_tokens * fit["prompt_fraction"]) + calibration_margin,
                         args.context_tokens - args.retrieval_output_tokens),
        "sustained": min(int(args.context_tokens * fit["sustained_prompt_fraction"]) + calibration_margin,
                         args.context_tokens - args.sustained_output_tokens),
    }
    calibration, cases = {}, []
    for kind, output in (("retrieval", args.retrieval_output_tokens), ("sustained", args.sustained_output_tokens)):
        lines, attempts = calibrate(args, kind, targets[kind], output)
        calibration[kind] = {"target_prompt_tokens": targets[kind], "filler_lines": lines, "attempts": attempts}
        if lines is None:
            continue
        repeats = args.retrieval_repeats if kind == "retrieval" else args.sustained_repeats
        cases.extend(call(args, kind, lines, output) for _ in range(repeats))

    minimum = math.ceil(args.context_tokens * args.minimum_prompt_fraction)
    retrieval = [case for case in cases if case["kind"] == "retrieval"]
    sustained = [case for case in cases if case["kind"] == "sustained"]
    coverage = all((case.get("actual_prompt_tokens") or 0) >= minimum for case in retrieval) and all((case.get("actual_prompt_tokens") or 0) >= int(args.context_tokens * fit["sustained_prompt_fraction"]) for case in sustained)
    retrieval_ok = len(retrieval) == args.retrieval_repeats and all(case.get("passed") for case in retrieval)
    sustained_ok = len(sustained) == args.sustained_repeats and all(case.get("passed") for case in sustained)
    decode = median(case.get("decode_tok_s") for case in sustained)
    useful = coverage and retrieval_ok and sustained_ok and decode is not None and decode >= args.minimum_decode_tok_s
    receipt = {
        "schema_version": "1.0", "kind": "raw-high-context-profile", "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "preset": args.preset, "model": args.model, "context_tokens": args.context_tokens,
        "active_server_context_tokens": reported_total,
        "active_server_parallel": parallel,
        "effective_request_context_tokens": effective_context,
        "requested_context_matches_server": effective_context == args.context_tokens if effective_context else None,
        "policy": {"prompt_cache_disabled": True, "unique_leading_request_nonce": True, "disable_thinking": args.disable_thinking, "minimum_decode_tok_s": args.minimum_decode_tok_s, "minimum_output_fraction": args.minimum_output_fraction, "calibration_margin_tokens": calibration_margin, "profile": args.profile},
        "calibration": calibration,
        "summary": {"useful": useful, "retrieval_passed": retrieval_ok, "sustained_passed": sustained_ok, "prompt_coverage_passed": coverage, "median_sustained_decode_tok_s": decode, "median_prompt_tok_s": median(case.get("prompt_tok_s") for case in cases), "median_sustained_draft_acceptance_rate": median(case.get("draft_acceptance_rate") for case in sustained)},
        "cases": cases,
    }
    output = Path(args.output) if args.output else Path(".local/bench") / args.preset / (datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S") + f"-ctx{args.context_tokens}.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(f"wrote raw high-context receipt to {output}")
    print("USEFUL" if useful else "NOT USEFUL", f"at {args.context_tokens} context")
    return 0 if useful else 2


if __name__ == "__main__":
    raise SystemExit(main())
