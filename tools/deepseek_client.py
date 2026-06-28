#!/usr/bin/env python3
"""
DeepSeek API client — drop-in replacement for ollama_client.py.

Usage:
  export DEEPSEEK_API_KEY="sk-..."
  python run_generation_eval_deepseek.py --model deepseek-chat --tasks ...

API docs: https://platform.deepseek.com/api-docs
"""
from __future__ import annotations

import json
import os
import urllib.request
from typing import Any, Dict, Optional


DEEPSEEK_API_BASE = "https://api.deepseek.com"


def deepseek_generate(
    model: str,
    prompt: str,
    system: Optional[str] = None,
    temperature: float = 0.0,
    timeout: float = 300.0,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Call DeepSeek Chat Completions API (OpenAI-compatible).

    Returns a dict matching ollama_client's interface:
      - "response": generated text
      - "prompt_eval_count": input tokens
      - "eval_count": output tokens
    """
    key = api_key or os.environ.get("DEEPSEEK_API_KEY", "")
    if not key:
        raise RuntimeError("Set DEEPSEEK_API_KEY environment variable or pass api_key=")

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "stream": False,
    }

    req = urllib.request.Request(
        f"{DEEPSEEK_API_BASE}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    # Map DeepSeek response to ollama-compatible format
    choice = data["choices"][0]
    usage = data.get("usage", {})
    return {
        "response": choice["message"]["content"],
        "prompt_eval_count": usage.get("prompt_tokens", 0),
        "eval_count": usage.get("completion_tokens", 0),
        "total_duration": 0,  # API doesn't report this
        "model": data.get("model", model),
    }
