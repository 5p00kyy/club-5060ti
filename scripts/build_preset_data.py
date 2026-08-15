#!/usr/bin/env python3
"""Build compact preset-first site data from reviewed manifests and evidence."""
import argparse
import json
from pathlib import Path


def load_all(directory):
    values = []
    for path in sorted(Path(directory).glob("*.json")):
        value = json.loads(path.read_text(encoding="utf-8"))
        value["_source_file"] = str(path)
        values.append(value)
    return values


def main():
    parser = argparse.ArgumentParser(description="Build preset-first site data without consuming raw benchmark rows.")
    parser.add_argument("--presets-dir", default="data/presets")
    parser.add_argument("--evidence-dir", default="data/evidence")
    parser.add_argument("--output", default="site/data/presets.json")
    args = parser.parse_args()
    presets = load_all(args.presets_dir)
    evidence = load_all(args.evidence_dir)
    by_preset = {}
    for item in evidence:
        by_preset.setdefault(item["preset"], []).append(item)
    cards = []
    for preset in presets:
        published = [item for item in by_preset.get(preset["id"], []) if item.get("status") == "published"]
        candidates = [item for item in by_preset.get(preset["id"], []) if item.get("status") == "candidate"]
        archived = [item for item in by_preset.get(preset["id"], []) if item.get("status") == "archived"]
        cards.append({
            "preset": preset,
            "published_evidence": published,
            "candidate_evidence": candidates,
            "archived_evidence": archived,
            "ready_for_default": preset.get("status") in {"recommended", "alternative"} and bool(published),
        })
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"presets": cards}, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(cards)} preset card(s) to {output}")


if __name__ == "__main__":
    raise SystemExit(main())
