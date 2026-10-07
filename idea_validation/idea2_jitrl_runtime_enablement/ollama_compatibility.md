# Ollama compatibility

## Stage-8C0.1 official client probes

The isolated jitrl_runtime environment used openai 3.26.0 and OpenAI(base_url="http://localhost:11434/v1", api_key=<non-empty dummy>). The existing qwen2.5:14b model was used. No model was pulled and no real API key was configured.

Exactly two standalone requests were made:

1. Text probe: returned exactly OK in 4.459678 seconds; usage was 34 prompt, 2 completion, 36 total tokens.
2. Strict JSON-schema probe: parsed as {"status": "OK"} in 0.215920 seconds; usage was 25 prompt, 10 completion, 35 total tokens.

Both returned choices[0].message.content. The probes did not depend on OpenRouter-only response fields.

This establishes OpenAI Python client compatibility for the tested text and structured-output contract. It does not claim that Ollama and OpenRouter are generally equivalent or that JitRL officially supports Ollama.
