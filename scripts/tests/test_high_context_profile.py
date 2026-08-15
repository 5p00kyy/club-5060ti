#!/usr/bin/env python3
"""Small end-to-end contract test for the local-only high-context runner."""
import json
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "run_high_context_profile.py"
NEEDLE = "CLUB-5060TI-HIGH-CONTEXT-NEEDLE-48291"


class Handler(BaseHTTPRequestHandler):
    cache_flags = []
    thinking_flags = []

    def log_message(self, *_args):
        pass

    def do_GET(self):
        if self.path == "/v1/models":
            self._send({"data": [{"id": "test-model", "status": {"args": ["--ctx-size", "16384"]}}]})
            return
        self.send_error(404)

    def do_POST(self):
        if self.path != "/v1/chat/completions":
            self.send_error(404)
            return
        request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        Handler.cache_flags.append(request.get("cache_prompt"))
        Handler.thinking_flags.append((request.get("chat_template_kwargs") or {}).get("enable_thinking"))
        prompt = request["messages"][0]["content"]
        retrieval = "reply with only the exact key" in prompt.lower()
        prompt_tokens = prompt.count("Benchmark context filler.") * 28 + 24
        # A published retrieval must be present in client-visible content; a
        # hidden reasoning trace alone is not a usable final answer.
        message = {"content": NEEDLE} if retrieval else {"content": "A" * 2000}
        self._send({
            "choices": [{"message": message}],
            "usage": {"prompt_tokens": prompt_tokens, "completion_tokens": 32 if retrieval else 1200},
            "timings": {"prompt_per_second": 300.0, "predicted_per_second": 20.0, "draft_n": 20, "draft_n_accepted": 15},
        })

    def _send(self, payload):
        body = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def run(server, output, disable_thinking=False):
    command = [
        sys.executable, str(SCRIPT), "--base-url", f"http://127.0.0.1:{server.server_port}/v1",
        "--model", "test-model", "--preset", "test-preset", "--context-tokens", "16384",
        "--output", str(output), "--timeout", "5",
        "--retrieval-output-tokens", "32", "--sustained-output-tokens", "3072",
    ]
    if disable_thinking:
        command.append("--disable-thinking")
    result = subprocess.run(command, text=True, capture_output=True)
    if result.returncode != 0:
        raise SystemExit(f"runner failed: {result.stdout}\n{result.stderr}")
    return json.loads(output.read_text())


def main():
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with tempfile.TemporaryDirectory() as directory:
            first = run(server, Path(directory) / "first.json")
            second = run(server, Path(directory) / "second.json", disable_thinking=True)
            for receipt in (first, second):
                assert receipt["summary"]["useful"] is True
                assert receipt["summary"]["prompt_coverage_passed"] is True
                assert receipt["effective_request_context_tokens"] == 16384
                assert receipt["summary"]["median_sustained_draft_acceptance_rate"] == 0.75
                assert receipt["requested_context_matches_server"] is True
                assert receipt["policy"]["sustained_output_tokens"] == 3072
                assert receipt["policy"]["minimum_generated_tokens"] == 1076
                assert receipt["policy"]["minimum_output_fraction"] is None
                assert len(receipt["cases"]) == 4
                assert len({case["request_nonce"] for case in receipt["cases"]}) == 4
                assert receipt["calibration"]["retrieval"]["filler_lines"] is not None
            assert second["policy"]["disable_thinking"] is True
            assert all(flag is False for flag in Handler.cache_flags)
            assert Handler.thinking_flags.count(None) >= 6
            assert Handler.thinking_flags.count(False) >= 6
    finally:
        server.shutdown()
    print("high-context profile contract test passed")


if __name__ == "__main__":
    main()
