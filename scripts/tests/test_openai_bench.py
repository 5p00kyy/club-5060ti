#!/usr/bin/env python3
"""Contract tests for OpenAI-compatible streaming and tool benchmark paths."""
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import sys
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import run_openai_bench as bench  # noqa: E402


class Handler(BaseHTTPRequestHandler):
    seen_headers = []
    seen_payloads = []

    def log_message(self, *_args):
        pass

    def do_GET(self):
        if self.path == "/v1/models":
            self._send_json({"data": [{"id": "test", "max_model_len": 32768}]})
            return
        self.send_error(404)

    def do_POST(self):
        Handler.seen_headers.append(dict(self.headers))
        if self.headers.get("Authorization") != "Bearer test-key":
            self.send_error(401)
            return
        payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        Handler.seen_payloads.append(payload)
        if self.path != "/v1/chat/completions":
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()
        events = [
            b": keepalive\n\n",
            b'data: {"choices":[{"delta":{"reasoning_content":"think"}}]}\n\n',
            b'data: {"choices":[{"delta":{"tool_calls":[{"index":0,"id":"call_1","type":"function","function":{"name":"record_benchmark_note","arguments":"{\\"note\\":\\"vLLM "}}]}}]}\n\n',
            b'data: not-json\n\n',
            b'data: {"choices":[{"delta":{"tool_calls":[{"index":0,"function":{"arguments":"tool-call contract passed\\",\\"severity\\":\\"info\\"}"}}]}}]}\n\n',
            b'data: {"choices":[{"delta":{"content":"done"}}]}\n\n',
            b'data: {"choices":[],"usage":{"prompt_tokens":12,"completion_tokens":4}}\n\n',
            b"data: [DONE]\n\n",
        ]
        for event in events:
            for index in range(0, len(event), 3):
                self.wfile.write(event[index:index + 3])
                self.wfile.flush()

    def _send_json(self, value):
        body = json.dumps(value).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    assert bench.infer_family("qwen3.8-27b-nvfp4") == "Qwen3.8"
    fragmented = [b"data: {\"a\":1}\r", b"\n\r\ndata: {\"b\":2}\n", b"\n", b"data: [DONE]\n\n"]
    assert list(bench.iter_sse_events(fragmented)) == ['{"a":1}', '{"b":2}', '[DONE]']
    response, meaningful = bench.parse_sse_events([
        '{"choices":[{"delta":{"reasoning":"v"}}]}',
        '{"choices":[{"delta":{"reasoning_content":"r"}}]}',
        'malformed',
        '{"choices":[{"delta":{"content":"c"}}]}',
        '{"choices":[],"usage":{"prompt_tokens":3,"completion_tokens":2}}',
    ])
    assert meaningful is True
    assert response["choices"][0]["message"]["content"] == "c"
    assert response["choices"][0]["message"]["reasoning_content"] == "vr"
    assert response["usage"]["prompt_tokens"] == 3
    missing, _ = bench.parse_sse_events(['{"choices":[{"delta":{"content":"no usage"}}]}', '[DONE]'])
    assert missing.get("usage") == {}
    rates = bench.server_metric_rates(
        {"vllm:request_prefill_kv_computed_tokens_sum": 10, "vllm:request_prefill_time_seconds_sum": 2,
         "vllm:request_generation_tokens_sum": 4, "vllm:request_decode_time_seconds_sum": 1},
        {"vllm:request_prefill_kv_computed_tokens_sum": 110, "vllm:request_prefill_time_seconds_sum": 4,
         "vllm:request_generation_tokens_sum": 24, "vllm:request_decode_time_seconds_sum": 2},
    )
    assert rates == {"server_prefill_tok_s": 50.0, "server_decode_tok_s": 20.0}
    assert bench.validate_tool_call_response({"choices": [{"message": {"tool_calls": [{"function": {"name": bench.TOOL_NAME, "arguments": json.dumps({"note": "vLLM tool-call contract passed", "severity": "info"})}}]}}]})

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base = f"http://127.0.0.1:{server.server_port}/v1"
        response, elapsed, metrics = bench.post_stream_json(
            base + "/chat/completions", {"model": "test", "messages": []}, 5, "test-key", "", {"x-benchmark-cache-policy": "no-reuse", "x-benchmark-run-nonce": "abc123"}
        )
        assert elapsed > 0
        assert response["usage"]["completion_tokens"] == 4
        assert metrics["client_ttft_seconds"] is not None
        assert metrics["client_decode_tok_s"] is not None
        assert metrics.get("server_prefill_tok_s") is None
        assert Handler.seen_payloads[0]["stream_options"]["include_usage"] is True
        assert Handler.seen_headers[0]["X-Benchmark-Cache-Policy"] == "no-reuse"
        assert Handler.seen_headers[0]["X-Benchmark-Run-Nonce"] == "abc123"
        try:
            bench.post_json(base + "/chat/completions", {}, 5, "wrong-key")
        except HTTPError as exc:
            assert exc.code == 401
        else:
            raise AssertionError("missing auth rejection")
    finally:
        server.shutdown()
    print("openai benchmark SSE/tool contract test passed")


if __name__ == "__main__":
    main()
