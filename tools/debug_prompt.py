#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ollama_client import ollama_generate
from run_generation_eval import load_jsonl

tasks = load_jsonl(Path(__file__).resolve().parent.parent / "data" / "tasks_realworld.jsonl")
print(f"Loaded {len(tasks)} tasks", flush=True)

prompts = (Path(__file__).resolve().parent.parent / "data" / "prompts_v1.md").read_text(encoding="utf-8")
tag = "```text"
close = "```"
system_start = prompts.index("## 1. System Prompt")
user_start = prompts.index("## 2. User Prompt Template")
system_block = prompts[prompts.index(tag, system_start) + 7:prompts.index(close, prompts.index(tag, system_start) + 7)].strip()
user_block = prompts[prompts.index(tag, user_start) + 7:prompts.index(close, prompts.index(tag, user_start) + 7)].strip()

print(f"System prompt: {len(system_block)} chars", flush=True)
print(f"User template: {len(user_block)} chars", flush=True)

task = tasks[0]
tid = task["task_id"]
prompt = user_block.format(
    task_id=tid,
    allowed_devices=", ".join(task["allowed_devices"]),
    prompt=task["prompt"],
)
print(f"\nTesting {tid}...", flush=True)
print(f"Prompt ({len(prompt)} chars):", flush=True)
print(prompt[:300], flush=True)

resp = ollama_generate("llama3.1:8b", prompt, system=system_block, temperature=0.0, timeout=60.0)
mir_text = resp.get("response", "")
print(f"\nLLM response ({len(mir_text)} chars):", flush=True)
print(mir_text[:300], flush=True)
