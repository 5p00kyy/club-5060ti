#!/usr/bin/env python3
"""Regression checks for contribution-to-explorer normalization."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import build_site_data as site_data  # noqa: E402


def main():
    source = ROOT / "data/results/community-3x5060ti-qwen38-27b-q8_0-204k.json"
    rows = json.loads(source.read_text(encoding="utf-8"))["results"]
    prepared = [site_data.prepare_site_item(row, source) for row in rows]

    assert len(prepared) == 4
    assert [row["_display_metrics"]["decode_tok_s"] for row in prepared] == [30.456, 30.465, 24.171, 24.263]
    assert all(row["_display_metrics"]["decode_source"] == "client" for row in prepared)

    short_rows = [row for row in prepared if row["benchmark"]["prompt_set"] == "short-chat"]
    long_rows = [row for row in prepared if row["benchmark"]["prompt_set"] == "long-retrieval"]
    assert all("prompt_tok_s" not in row["_display_metrics"] for row in short_rows)
    assert [row["_display_metrics"]["prompt_tok_s"] for row in long_rows] == [479.584, 479.541]
    assert all(row["_display_metrics"]["prompt_source"] == "client-ttft-derived" for row in long_rows)

    assert "_repeat_prompt_key" not in short_rows[0]
    assert "_repeat_prompt_key" not in short_rows[1]
    assert long_rows[0]["_repeat_prompt_key"] == long_rows[1]["_repeat_prompt_key"]

    precedence = {
        "metrics": {
            "decode_tok_s": 10,
            "client_decode_tok_s": 20,
            "server_decode_tok_s": 30,
            "prompt_tok_s": 40,
            "server_prefill_tok_s": 50,
        },
        "benchmark": {},
    }
    assert site_data.display_metrics(precedence) == {
        "decode_tok_s": 10.0,
        "decode_source": "reported",
        "prompt_tok_s": 40.0,
        "prompt_source": "reported",
    }

    print("site contribution normalization test passed")


if __name__ == "__main__":
    main()
