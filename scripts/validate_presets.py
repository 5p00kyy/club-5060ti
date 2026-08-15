#!/usr/bin/env python3
"""Validate canonical preset manifests without promoting them to public evidence."""
import argparse
import json
import sys
from pathlib import Path

REQUIRED = {"schema_version", "id", "title", "status", "provenance", "purpose", "hardware", "runtime", "model", "serving", "profile", "context"}
STATUSES = {"candidate", "recommended", "alternative", "experimental", "archived"}
PROVENANCE = {"seed-tested", "community-verified", "community-submitted"}
LANES = {"1x5060ti", "2x5060ti", "multi-5060ti", "mixed-5060ti-cuda", "other-cuda"}


def validate(path: Path):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"{path}: invalid JSON: {exc}"]
    errors = []
    if not isinstance(value, dict):
        return [f"{path}: manifest must be an object"]
    missing = sorted(REQUIRED - set(value))
    if missing:
        errors.append(f"{path}: missing fields: {', '.join(missing)}")
    if value.get("schema_version") != "1.0":
        errors.append(f"{path}: schema_version must be 1.0")
    if value.get("status") not in STATUSES:
        errors.append(f"{path}: invalid status")
    if value.get("provenance") not in PROVENANCE:
        errors.append(f"{path}: invalid provenance")
    hardware = value.get("hardware") or {}
    if hardware.get("lane") not in LANES:
        errors.append(f"{path}: invalid hardware lane")
    if not isinstance(hardware.get("gpu_count"), int) or hardware.get("gpu_count") < 1:
        errors.append(f"{path}: hardware.gpu_count must be a positive integer")
    runtime = value.get("runtime") or {}
    preset_file = runtime.get("preset_file")
    if not preset_file or not Path(preset_file).is_file():
        errors.append(f"{path}: runtime.preset_file must reference a tracked file")
    elif runtime.get("preset_section") and f"[{runtime['preset_section']}]" not in Path(preset_file).read_text(encoding="utf-8"):
        errors.append(f"{path}: runtime.preset_section is not present in runtime.preset_file")
    profile = value.get("profile")
    if not profile or not Path(profile).is_file():
        errors.append(f"{path}: profile must reference a tracked file")
    context = value.get("context") or {}
    target, minimum = context.get("target_tokens"), context.get("minimum_useful_tokens")
    if not isinstance(target, int) or not isinstance(minimum, int) or minimum < 1 or target < minimum:
        errors.append(f"{path}: context target/minimum must be positive and target >= minimum")
    if value.get("status") == "recommended" and value.get("provenance") == "community-submitted":
        errors.append(f"{path}: community-submitted presets cannot be recommended without verification")
    if value.get("status") in {"candidate", "recommended", "alternative"} and value.get("provenance") == "seed-tested" and not value.get("known_evidence"):
        errors.append(f"{path}: active seed-tested presets require known evidence")
    return errors


def main():
    parser = argparse.ArgumentParser(description="Validate data/presets/*.json manifests.")
    parser.add_argument("paths", nargs="*", default=["data/presets"])
    args = parser.parse_args()
    files = []
    for raw in args.paths:
        path = Path(raw)
        files.extend(sorted(path.glob("*.json")) if path.is_dir() else [path])
    errors = [error for path in files for error in validate(path)]
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"validated {len(files)} preset manifest(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
