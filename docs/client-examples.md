# Client Examples

Both vLLM and llama.cpp can expose an OpenAI-compatible API. Adjust the base URL and model name for your server.

## Endpoint Shapes

Use one served model name per endpoint and keep it stable in your client config.

| Runtime | Example base URL | Example model name | Notes |
| --- | --- | --- | --- |
| vLLM | `http://your-host:8000/v1` | `qwen3.8-27b-nvfp4` | Recommended dual-card OpenAI-compatible serving path; 122,880 context and one active sequence. |
| llama.cpp router | `http://your-host:8080/v1` | `Qwen3.6-27B` | Useful for GGUF presets and model switching. |
| llama.cpp direct test server | `http://your-host:18080/v1` | `qwen35-9b-mtp-q4-single` | Good for one-off benchmarks; do not leave exposed. |

If a client asks for an API key and your local server does not enforce one, use a placeholder such as `not-used`.

## curl

~~~bash
curl -s http://127.0.0.1:8000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "qwen3.8-27b-nvfp4",
    "messages": [{"role": "user", "content": "Say 5060 Ti ready."}],
    "temperature": 0,
    "max_tokens": 128
  }'
~~~

## Python

~~~python
from openai import OpenAI

client = OpenAI(base_url="http://127.0.0.1:8000/v1", api_key="not-used")

response = client.chat.completions.create(
    model="qwen3.8-27b-nvfp4",
    messages=[{"role": "user", "content": "Say 5060 Ti ready."}],
    temperature=0,
    max_tokens=128,
)

print(response.choices[0].message.content)
~~~

## Shared Client Field Map

Most OpenAI-compatible clients ask for the same pieces under slightly different labels:

| Client label | Value |
| --- | --- |
| API base URL / OpenAI base URL | `http://your-host:8000/v1` for vLLM, or `http://your-host:8080/v1` for llama.cpp |
| API key | Placeholder if unauthenticated, otherwise your local server key |
| Model | The served model name, for example `qwen3.8-27b-nvfp4` or `Qwen3.6-27B` |
| Chat endpoint | `/v1/chat/completions` |
| Streaming | Test both on and off; some clients fail only on streaming/tool output |
| Max output tokens | Start at 4096 for coding; raise to 8192+ for thinking/reasoning models |

## Open WebUI

Use an OpenAI-compatible connection:

- API base URL: http://your-host:8000/v1
- API key: any placeholder if your server does not enforce auth
- Model: qwen3.8-27b-nvfp4 or your served model name

## Coding Agents

For coding agents and tools, start with explicit output budgets. Qwen thinking/reasoning can consume the full generation limit before returning final content.

Good starting points:

- no thinking: 1024 max tokens
- light coding help: 4096 max tokens
- harder reasoning: 8192+ max tokens

If your client supports extra request body fields for vLLM/Qwen, no-thinking mode is usually:

~~~json
{
  "chat_template_kwargs": {
    "enable_thinking": false
  }
}
~~~

## OpenCode

OpenCode supports custom OpenAI-compatible providers through `opencode.json`. For local vLLM or llama.cpp endpoints, use the OpenAI-compatible provider package for `/v1/chat/completions`.

Example `opencode.json`:

~~~json
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "club5060ti-vllm": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "club-5060ti vLLM",
      "options": {
        "baseURL": "http://your-host:8000/v1",
        "apiKey": "not-used"
      },
      "models": {
        "qwen3.8-27b-nvfp4": {
          "name": "Qwen3.8 27B NVFP4/MTP",
          "limit": {
            "context": 122880,
            "output": 8192
          }
        }
      }
    },
    "club5060ti-llamacpp": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "club-5060ti llama.cpp",
      "options": {
        "baseURL": "http://your-host:8080/v1",
        "apiKey": "not-used"
      },
      "models": {
        "Qwen3.6-27B": {
          "name": "Qwen3.6 27B GGUF",
          "limit": {
            "context": 65536,
            "output": 8192
          }
        }
      }
    }
  },
  "model": "club5060ti-vllm/qwen3.8-27b-nvfp4"
}
~~~

Notes:

- Use the vLLM endpoint first for coding-agent workflows if you need tool calling and long-context serving.
- Use the llama.cpp endpoint for GGUF model comparisons or a simpler local server.
- If OpenCode shows the provider but not the model, verify that the provider ID in `/connect` matches the provider ID in `opencode.json`.
- If streaming works for short replies but fails during tool use, capture server logs and retry once with streaming disabled if the client allows it.

## Pi, Cline, Cursor, And Similar Clients

For clients with a generic OpenAI-compatible provider screen, use the shared field map above.

Practical starting config:

~~~text
Provider: OpenAI-compatible / custom OpenAI
Base URL: http://your-host:8000/v1
API key: not-used
Model: qwen3.8-27b-nvfp4
Max output tokens: 4096-8192
Streaming: on, then retest off if tool calls disconnect
~~~

For llama.cpp:

~~~text
Provider: OpenAI-compatible / custom OpenAI
Base URL: http://your-host:8080/v1
API key: not-used
Model: Qwen3.6-27B
Max output tokens: 4096-8192
Streaming: test before relying on long tool output
~~~

The important thing is to use the exact served model name returned by:

~~~bash
curl -s http://your-host:8000/v1/models
curl -s http://your-host:8080/v1/models
~~~

## Codex CLI

Codex CLI's current public configuration is centered on OpenAI/Responses-style providers. vLLM and llama.cpp commonly expose `/v1/chat/completions`, so they are not always a direct drop-in for Codex CLI without a bridge or gateway that speaks the API shape your Codex build expects.

If your Codex build or gateway supports a custom local provider, the fields to map are still:

~~~toml
model = "qwen36-27b-nvfp4-mtp"
model_provider = "club5060ti"

[model_providers.club5060ti]
name = "club-5060ti local"
base_url = "http://your-host:8000/v1"
env_key = "CLUB5060TI_API_KEY"
~~~

Then set a placeholder key if your local endpoint requires the variable:

~~~bash
export CLUB5060TI_API_KEY=not-used
~~~

Before relying on Codex for real edits, run a short chat, a streaming response, and a tool-heavy coding task. Treat failures here as client/gateway compatibility issues until a plain `curl` request to the same endpoint also fails.
