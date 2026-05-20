#!/usr/bin/env python3
from __future__ import annotations

import json
import urllib.request
from typing import Any, Dict, Optional


def ollama_generate(
    model: str,
    prompt: str,
    system: Optional[str] = None,
    temperature: float = 0.0,
    timeout: float = 900.0,
) -> Dict[str, Any]:
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
        },
    }
    if system:
        payload["system"] = system
    req = urllib.request.Request(
        "http://127.0.0.1:11434/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))
