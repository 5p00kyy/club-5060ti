#!/usr/bin/env python3
"""Deterministic contract tests for run_stack_quality.py."""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import threading
from argparse import Namespace
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "run_stack_quality.py"
sys.path.insert(0, str(ROOT / "scripts"))
import run_stack_quality as runner  # noqa: E402


class Handler(BaseHTTPRequestHandler):
    nonces: list[str] = []
    requests: list[dict] = []

    def log_message(self, *_args):
        pass

    def do_POST(self):
        if self.headers.get("Authorization") != "Bearer test-key":
            self.send_response(401)
            self.end_headers()
            return
        payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        Handler.requests.append(payload)
        messages = payload.get("messages") or []
        prompt = messages[-1].get("content", "") if messages else payload.get("prompt", "")
        if self.path == "/tokenize":
            self._send({"count": max(1, len(prompt) // 4), "tokens": []})
            return
        if "Unique run nonce:" in prompt:
            Handler.nonces.append(re.search(r"Unique run nonce: ([a-f0-9]+)", prompt).group(1))
        if payload.get("tools"):
            message = {"tool_calls": [{"id": "call_test", "type": "function", "function": {"name": runner.TOOL_NAME, "arguments": json.dumps(runner.expected_tool())}}]}
        elif "Three bags" in prompt:
            message = {"content": "FINAL: 20"}
        elif "f(n)=n^2+n" in prompt:
            message = {"content": "FINAL: 66"}
        elif "van drives" in prompt:
            message = {"content": "FINAL: 50"}
        elif "remainders 2 modulo 3" in prompt:
            message = {"content": "FINAL: 5"}
        elif "fair coin" in prompt:
            message = {"content": "FINAL: 4/7"}
        elif "A finished after B" in prompt:
            message = {"content": "FINAL: UNKNOWN"}
        elif "Alice says Bob" in prompt:
            message = {"content": "FINAL: Alice"}
        elif "print([x*x" in prompt:
            message = {"content": "FINAL: [1, 4, 9]"}
        elif "setTimeout" in prompt:
            message = {"content": "FINAL: 3 3 3"}
        elif "sum(i*j" in prompt:
            message = {"content": "FINAL: 31"}
        elif "Write SQL" in prompt:
            message = {"content": "FINAL: SELECT customer_id, SUM(amount) FROM orders GROUP BY customer_id"}
        elif "exactly five words" in prompt:
            message = {"content": "FINAL: sky calm brisk jump soft"}
        elif "Sort dog" in prompt:
            message = {"content": "FINAL: ant, bat, cat, dog"}
        elif "keys status,count,items" in prompt:
            message = {"content": '{"status":"ok","count":3,"items":["red","green","blue"]}'}
        elif "Mira from Brisbane" in prompt:
            message = {"content": '{"name":"Mira","city":"Brisbane","tickets":2}'}
        elif "organelle" in prompt:
            message = {"content": "FINAL: C"}
        elif "net force" in prompt:
            message = {"content": "FINAL: B"}
        elif "99% sensitivity" in prompt:
            message = {"content": "FINAL: C"}
        elif "PRIVATE_IP_VALUE" in prompt:
            message = {"content": "FINAL: redact private values and omit local paths from public reports."}
        elif "unknown person's bank" in prompt:
            message = {"content": "FINAL: UNKNOWN"}
        elif "last three decimal" in prompt:
            message = {"content": "FINAL: 049"}
        elif "n mod 7=3" in prompt:
            message = {"content": "FINAL: 346"}
        elif "length-6 strings" in prompt:
            message = {"content": "FINAL: 160"}
        elif "largest among its first three" in prompt:
            message = {"content": "FINAL: 1/3"}
        elif "x+y=11" in prompt:
            message = {"content": "FINAL: 3"}
        elif "positive divisors" in prompt:
            message = {"content": "FINAL: 30"}
        elif "Exactly one of A, B, C" in prompt:
            message = {"content": "FINAL: B"}
        elif "early, middle, and late markers" in prompt:
            markers = [re.search(rf"{name} marker: (\S+)", prompt).group(1) for name in ("Early", "Middle", "Late")]
            message = {"content": json.dumps(markers)}
        else:
            message = {"content": "FINAL: 31"}
        self._send({"choices": [{"message": message, "finish_reason": "stop"}], "usage": {"prompt_tokens": max(10, len(prompt) // 4), "completion_tokens": 8}, "timings": {"prompt_per_second": 100.0, "predicted_per_second": 20.0}})

    def _send(self, body):
        data = json.dumps(body).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def main():
    assert runner.check_tool({"tool_calls": [{"function": {"name": runner.TOOL_NAME, "arguments": json.dumps(runner.expected_tool())}}]})[0]
    assert runner.check_json({"a": 2})({"content": '{"a":1}'})[0] is False
    sample = f"Bearer {runner.SECRET_SAMPLE} at {runner.PRIVATE_IP_SAMPLE}"
    assert runner.sanitize_text(sample) == "Bearer <redacted> at <private-endpoint>"

    cases = runner.base_cases()
    reasoning_categories = {"arithmetic", "math", "logic", "code_reasoning", "knowledge"}
    reasoning = [case for case in cases if case["category"] in reasoning_categories]
    assert reasoning and all(case["thinking"] for case in reasoning)
    assert all(case["max_tokens"] == runner.THINKING_MAX_TOKENS for case in reasoning)
    assert all("Reason internally as needed" in case["prompt"] for case in reasoning)
    ordinary = [case for case in cases if case["category"] == "instruction" or case["id"] == "unknown_secret"]
    assert ordinary and all(not case["thinking"] for case in ordinary)
    assert all("output only the requested final answer" in case["prompt"] for case in ordinary)
    assert all("valid compact JSON" in case["prompt"] for case in cases if case["category"] == "structured_output")
    privacy = next(case for case in cases if case["id"] == "privacy_robustness")
    assert "with the brief explanation on that same line" in privacy["prompt"] and not privacy["thinking"]
    thinking = runner.thinking_cases()
    assert {case["max_tokens"] for case in thinking} == {runner.THINKING_MAX_TOKENS}
    assert runner.THINKING_MAX_TOKENS > 4096
    exact_case = next(case for case in cases if case["id"] == "arith_bags")
    passed, details = runner.diagnose_case(exact_case, {"content": "FINAL: 20", "finish_reason": "stop"})
    assert passed and details["answer_correct"] and details["completion_contract"]
    passed, details = runner.diagnose_case(exact_case, {"content": "work\nFINAL: 20", "finish_reason": "stop"})
    assert not passed and details["answer_correct"] and not details["completion_contract"]
    echoed = exact_case["prompt"] + "\nFINAL: 20"
    passed, details = runner.diagnose_case(exact_case, {"content": echoed, "finish_reason": "stop"})
    assert not passed and not details["answer_correct"] and not details["completion_contract"]
    passed, details = runner.diagnose_case(exact_case, {"content": "FINAL: 20", "finish_reason": "length"})
    assert not passed and details["answer_correct"] and not details["completion_contract"]

    tokenizer_calls = []
    original_request_json = runner.request_json
    def llama_contract(url, payload, timeout, api_key):
        tokenizer_calls.append(payload)
        if "prompt" in payload:
            return {"tokens": []}, 0.0
        return {"tokens": [1, 2, 3]}, 0.0
    runner.request_json = llama_contract
    count, method = runner.tokenize_count(Namespace(base_url="http://127.0.0.1:1/v1", model="test-model", timeout=5, api_key=""), "x" * 128)
    runner.request_json = original_request_json
    assert count == 3 and method == "llama.cpp /tokenize"
    assert tokenizer_calls[0].get("prompt") and tokenizer_calls[1].get("content") and tokenizer_calls[1]["add_special"] is False

    original_request_json = runner.request_json
    runner.request_json = lambda *_args, **_kwargs: ({"count": 1, "tokens": []}, 0.0)
    guarded = runner.calibrate_context_case(
        Namespace(base_url="http://127.0.0.1:1/v1", model="test-model", timeout=5, api_key="test-key"),
        96_000,
        "guard-test",
    )
    runner.request_json = original_request_json
    assert guarded["filler_repeats"] < 96_000 * 2
    assert "invalid token count" in guarded["calibration_method"]
    try:
        runner.context_case(runner.MAX_CONTEXT_TARGET_TOKENS + 1, "too-large")
    except ValueError:
        pass
    else:
        raise AssertionError("unsafe context target was accepted")

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    with tempfile.TemporaryDirectory() as td:
        output = Path(td) / "quality"
        command = [sys.executable, str(SCRIPT), "--base-url", f"http://127.0.0.1:{server.server_port}/v1", "--api-key", "test-key", "--model", "test-model", "--stack-id", "mock-stack", "--output-dir", str(output), "--context-bands", "256,512", "--repeats", "2", "--thinking-repeats", "2", "--thinking-seeds", "44,45", "--timeout", "5"]
        result = subprocess.run(command, text=True, capture_output=True)
        if result.returncode != 0:
            raise SystemExit(result.stdout + "\n" + result.stderr)
        artifact = json.loads((output / "results.json").read_text())
        summary = artifact["summary"]
        assert summary["passed"] == summary["total"]
        assert summary["answer_correct"] == summary["total"]
        assert summary["completion_contract"] == summary["total"]
        assert summary["total"] == 21 * 2 + 8 * 2 + 2 * 2
        assert set(summary["by_category"]) >= {"arithmetic", "tool_call", "thinking_reasoning", "long_context"}
        assert all(bucket["answer_correct"] == bucket["total"] for bucket in summary["by_category"].values())
        assert all(bucket["completion_contract"] == bucket["total"] for bucket in summary["by_category"].values())
        assert len(Handler.nonces) == 4
        assert len(set(Handler.nonces)) == 4
        assert artifact["metadata"]["base_url"].startswith("http://<private-endpoint>")
        assert "test-key" not in (output / "results.json").read_text()
        checkpoint_records = [json.loads(line) for line in (output / "records.jsonl").read_text().splitlines()]
        assert checkpoint_records == artifact["records"]
        assert "test-key" not in (output / "records.jsonl").read_text()
        for record in artifact["records"]:
            assert {"case_id", "category", "stack_id", "passed", "request", "raw_response", "usage", "timings"}.issubset(record)
        summary_file = json.loads((output / "summary.json").read_text())
        assert summary_file["summary"] == summary
        assert artifact["suite_id"] == runner.SUITE_ID
        assert artifact["suite_version"] == runner.SUITE_VERSION
        assert artifact["evidence_semantics_version"] == runner.EVIDENCE_SEMANTICS_VERSION
        assert all({"answer_correct", "completion_contract", "suite_version"}.issubset(record) for record in artifact["records"])

        # A V1 receipt must not be silently replaced by V2 evidence.
        stale = output / "stale"
        stale.mkdir()
        (stale / "results.json").write_text(json.dumps({"schema_version": "1.0"}))
        try:
            runner.ensure_output_dir_version(stale)
        except ValueError:
            pass
        else:
            raise AssertionError("unversioned receipt was accepted")

    # Auth failure is exercised directly and must not become a successful result.
    try:
        runner.request_json(f"http://127.0.0.1:{server.server_port}/v1/chat/completions", {"model": "x"}, 1, "wrong-key")
    except Exception as exc:
        assert getattr(exc, "code", None) == 401
    else:
        raise AssertionError("wrong API key unexpectedly succeeded")
    server.shutdown()
    print("stack quality contract test passed")


if __name__ == "__main__":
    main()
