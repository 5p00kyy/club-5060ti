#!/usr/bin/env python3
"""Run the high-context profile across a context ladder using a dedicated server.

The supplied launch template must contain {context_tokens}. All other serving
settings stay fixed, making each rung evidence for the same preset. This script
owns only the child process it starts; do not point it at a shared router port.
"""
import argparse
import json
import os
import shlex
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILE_RUNNER = ROOT / "scripts" / "run_high_context_profile.py"


def model_ready(base_url, model, timeout):
    try:
        with urllib.request.urlopen(base_url.rstrip("/") + "/models", timeout=5) as response:
            data = json.loads(response.read().decode())
    except Exception:
        return False
    return any(item.get("id") == model for item in data.get("data") or [])


def write_failure(root, preset, model, context, failure):
    output = root / (datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S") + f"-ctx{context}-startup-failed.json")
    payload = {
        "schema_version": "1.0",
        "kind": "raw-high-context-profile",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "preset": preset,
        "model": model,
        "context_tokens": context,
        "summary": {
            "useful": False,
            "retrieval_passed": False,
            "sustained_passed": False,
            "prompt_coverage_passed": False,
            "median_sustained_decode_tok_s": None,
            "median_prompt_tok_s": None,
        },
        "failure": failure,
        "cases": [],
    }
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return output


def stop(process):
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=20)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=10)


def main():
    parser = argparse.ArgumentParser(description="Walk a context ladder against a dedicated, per-tier server process.")
    parser.add_argument("--base-url", required=True, help="Dedicated endpoint, e.g. http://127.0.0.1:18081/v1")
    parser.add_argument("--model", required=True)
    parser.add_argument("--preset", required=True)
    parser.add_argument("--server-command-template", required=True, help="Launch command with literal {context_tokens} placeholder.")
    parser.add_argument("--profile", default="data/benchmark-profiles/high-context.json")
    parser.add_argument("--output-root", default="", help="Defaults to .local/bench/<preset>.")
    parser.add_argument("--startup-timeout", type=int, default=300)
    parser.add_argument("--request-timeout", type=int, default=1800)
    parser.add_argument("--keep-going", action="store_true", help="Continue upward after an unusable rung; default stops at the first failure.")
    parser.add_argument("--start-at", type=int, default=None, help="Begin at this declared context tier, useful after an existing higher-tier check.")
    args = parser.parse_args()

    if "{context_tokens}" not in args.server_command_template:
        raise SystemExit("--server-command-template must include {context_tokens}; do not hide context changes")
    profile = json.loads(Path(args.profile).read_text(encoding="utf-8"))
    tiers = profile.get("context_ladder") or []
    if not tiers or any(not isinstance(tier, int) or tier < 1 for tier in tiers):
        raise SystemExit("profile has no valid context_ladder")
    if args.start_at is not None:
        if args.start_at not in tiers:
            raise SystemExit("--start-at must be a tier declared by the profile")
        tiers = tiers[tiers.index(args.start_at):]
    root = Path(args.output_root) if args.output_root else Path(".local/bench") / args.preset
    root.mkdir(parents=True, exist_ok=True)

    # A live endpoint is evidence that this is not a safe dedicated test port.
    if model_ready(args.base_url, args.model, 5):
        raise SystemExit("endpoint already serves the target model; use a dedicated test endpoint so this script never replaces a shared service")

    outcomes = []
    for context in tiers:
        command = shlex.split(args.server_command_template.format(context_tokens=context))
        log_path = root / (datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S") + f"-ctx{context}-server.log")
        with log_path.open("w", encoding="utf-8") as log:
            process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
            deadline = time.monotonic() + args.startup_timeout
            while time.monotonic() < deadline and process.poll() is None and not model_ready(args.base_url, args.model, 5):
                time.sleep(1)
            if not model_ready(args.base_url, args.model, 5):
                state = f"server did not become ready (exit={process.poll()}); see {log_path.name}"
                stop(process)
                receipt = write_failure(root, args.preset, args.model, context, state)
                outcomes.append((context, False, receipt))
                print(f"NOT READY at {context}: {receipt}")
                if not args.keep_going:
                    break
                continue
            command = [
                sys.executable, str(PROFILE_RUNNER), "--base-url", args.base_url, "--model", args.model,
                "--preset", args.preset, "--context-tokens", str(context), "--profile", args.profile,
                "--timeout", str(args.request_timeout),
                "--output", str(root / (datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S") + f"-ctx{context}.json")),
            ]
            result = subprocess.run(command)
            stop(process)
            receipt = Path(command[-1])
            passed = result.returncode == 0
            outcomes.append((context, passed, receipt))
            if not passed and not args.keep_going:
                break

    highest = max((context for context, passed, _ in outcomes if passed), default=None)
    print(f"highest useful context: {highest if highest else 'none'}")
    return 0 if highest else 2


if __name__ == "__main__":
    raise SystemExit(main())
