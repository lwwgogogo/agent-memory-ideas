# Ollama compatibility audit

## Server and model

- Ollama version: 0.5.12
- OpenAI-compatible base URL: http://localhost:11434/v1
- Existing model: qwen2.5:14b, the smallest installed text generator
- No model was pulled
- Before request 1, /api/ps reported no loaded model

Exactly two standalone model requests were made. No JitRL episode was run.

## Request 1: required basic probe

The request used raw HTTP because the official OpenAI Python client is missing from agentmem_lab and installation was forbidden.

Prompt: Respond with exactly: OK

Settings: temperature 0, max_tokens 16, stream false.

- HTTP 200
- 4.388890 seconds
- content exactly OK
- finish_reason stop
- usage: 34 prompt, 2 completion, 36 total tokens
- schema included id, object, created, model, choices, and usage

## Request 2: JitRL field probe

The final allowed request added strict response_format json_schema, logprobs true, and top_logprobs 3.

- HTTP 200
- 0.242299 seconds
- content parsed as {"status": "OK"}
- usage: 24 prompt, 10 completion, 34 total tokens
- JSON schema was honored
- logprobs fields were accepted, but no logprobs object was returned

## Interpretation

The endpoint provides the chat-completions object and structured output required by verbalized-confidence action generation. Native JitRL hardcodes OpenRouter, so a constructor-level base URL adapter is needed. Default verbalized mode does not consume response logprobs. Logit mode does and is unsupported by the observed response.

The endpoint evidence is positive, but it is not the mandated OpenAI Python-client probe. The full compatibility gate therefore does not pass.
