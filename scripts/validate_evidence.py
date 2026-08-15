#!/usr/bin/env python3
"""Validate reviewed public evidence bundles for canonical presets."""
import argparse
import json
import sys
from pathlib import Path

REQUIRED = {"schema_version", "id", "preset", "status", "provenance", "context", "evidence", "caveats"}
STATUSES = {"candidate", "published", "archived"}
PROVENANCE = {"seed-tested", "community-verified"}
FORBIDDEN_RECEIPT_FIELDS = {"request_nonce", "response", "reasoning_response"}


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def find_forbidden_receipt_fields(value, prefix=""):
    found = []
    if isinstance(value, dict):
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else key
            if key in FORBIDDEN_RECEIPT_FIELDS:
                found.append(path)
            found.extend(find_forbidden_receipt_fields(child, path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(find_forbidden_receipt_fields(child, f"{prefix}[{index}]"))
    return found


def main():
    parser = argparse.ArgumentParser(description="Validate data/evidence/*.json bundles.")
    parser.add_argument("paths", nargs="*", default=["data/evidence"])
    args = parser.parse_args()
    presets = {path.stem for path in Path("data/presets").glob("*.json")}
    files = []
    for raw in args.paths:
        path = Path(raw)
        files.extend(sorted(path.glob("*.json")) if path.is_dir() else [path])
    errors = []
    for path in files:
        try:
            value = load(path)
        except Exception as exc:
            errors.append(f"{path}: invalid JSON: {exc}")
            continue
        missing = sorted(REQUIRED - set(value)) if isinstance(value, dict) else sorted(REQUIRED)
        if missing:
            errors.append(f"{path}: missing fields: {', '.join(missing)}")
            continue
        if value.get("schema_version") != "1.0": errors.append(f"{path}: schema_version must be 1.0")
        if value.get("status") not in STATUSES: errors.append(f"{path}: invalid status")
        if value.get("provenance") not in PROVENANCE: errors.append(f"{path}: invalid provenance")
        if value.get("preset") not in presets: errors.append(f"{path}: unknown preset {value.get('preset')!r}")
        context = value.get("context") or {}
        if not isinstance(context.get("highest_useful_tokens"), int) or context["highest_useful_tokens"] < 1:
            errors.append(f"{path}: context.highest_useful_tokens must be positive")
        actual = context.get("actual_prompt_tokens")
        if not isinstance(actual, (int, dict)):
            errors.append(f"{path}: context.actual_prompt_tokens must be an integer or workload map")
        checks = (value.get("evidence") or {}).get("checks") or {}
        if not isinstance(checks.get("retrieval_repeats"), int) or checks["retrieval_repeats"] < 1:
            errors.append(f"{path}: evidence.checks.retrieval_repeats must be positive")
        sustained = checks.get("sustained_generation_repeats")
        if not isinstance(sustained, int) or sustained < 0:
            errors.append(f"{path}: evidence.checks.sustained_generation_repeats must be zero or positive")
        if value.get("status") == "published" and sustained < 1:
            errors.append(f"{path}: published evidence requires sustained-generation checks")
        metrics = (value.get("evidence") or {}).get("metrics") or {}
        for name in ("median_prefill_tok_s", "median_decode_tok_s"):
            if not isinstance(metrics.get(name), (int, float)) or metrics[name] <= 0:
                errors.append(f"{path}: evidence.metrics.{name} must be positive")
        receipts = value.get("source_receipts") or []
        if value.get("status") == "published" and not receipts:
            errors.append(f"{path}: published evidence requires source_receipts")
        for receipt in receipts:
            receipt_path = Path(receipt) if isinstance(receipt, str) else None
            if receipt_path is None or not receipt_path.is_file():
                errors.append(f"{path}: source receipt is missing: {receipt!r}")
                continue
            try:
                forbidden = find_forbidden_receipt_fields(load(receipt_path))
            except Exception as exc:
                errors.append(f"{path}: source receipt is invalid JSON: {receipt!r}: {exc}")
                continue
            if forbidden:
                errors.append(f"{path}: source receipt contains private/raw fields: {receipt!r}: {', '.join(forbidden)}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"validated {len(files)} evidence bundle(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
