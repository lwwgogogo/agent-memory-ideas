"""Transport-only OpenAI constructor adapter for local Ollama."""

from __future__ import annotations

import os
from typing import Any, Callable

DEFAULT_BASE_URL = "http://localhost:11434/v1"
DEFAULT_API_KEY = "ollama"
DEFAULT_MODEL = "qwen2.5:14b"


def backend_settings() -> dict[str, str]:
    return {
        "base_url": os.environ.get("JITRL_OPENAI_BASE_URL", DEFAULT_BASE_URL),
        "api_key": os.environ.get("JITRL_OPENAI_API_KEY", DEFAULT_API_KEY),
        "model": os.environ.get("JITRL_OLLAMA_MODEL", DEFAULT_MODEL),
    }


def patch_openai_constructor() -> Callable[..., Any]:
    """Redirect JitRL's OpenAI client construction without changing its logic."""
    import openai

    original = openai.OpenAI
    settings = backend_settings()

    def ollama_openai(*args: Any, **kwargs: Any) -> Any:
        kwargs["base_url"] = settings["base_url"]
        kwargs["api_key"] = settings["api_key"]
        return original(*args, **kwargs)

    openai.OpenAI = ollama_openai
    return original
