#!/usr/bin/env python3
"""Simple runner for real-world tasks - one by one."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ollama_client import ollama_generate
from run_generation_eval import compile_expected_payloads, evaluate_candidate, expected_signature, load_jsonl

tasks = load_jsonl(Path(__file__).resolve().parent.parent / "data" / "tasks_realworld.jsonl")
print(f"Loaded {len(tasks)} tasks", flush=True)

expected_map = compile_expected_payloads(tasks)
print("compiled", flush=True)

prompts = (Path(__file__).resolve().parent.parent / "data" / "prompts_v1.md").read_text(encoding="utf-8")
tag = "```text"
end = "```"
system_start = prompts.index("## 1. System Prompt")
user_start = prompts.index("## 2. User Prompt Template")
system_block = prompts[prompts.index(tag, system_start) + 7:prompts.index(end, prompts.index(tag, system_start) + 7)].strip()
user_block = prompts[prompts.index(tag, user_start) + 7:prompts.index(end, prompts.index(tag, user_start) + 7)].strip()

sig_cache = {t["task_id"]: expected_signature(t) for t in tasks}

results = []
for i, task in enumerate(tasks):
    tid = task["task_id"]
    prompt = user_block.format(
        task_id=tid,
        allowed_devices=", ".join(task["allowed_devices"]),
        prompt=task["prompt"],
    )
    print(f"[{i+1}/{len(tasks)}] {tid}...", flush=True)
    try:
        resp = ollama_generate("llama3.1:8b", prompt, system=system_block, temperature=0.0, timeout=120.0)
        mir_text = resp.get("response", "")
        result = evaluate_candidate(task, expected_map[tid], sig_cache[tid], 1, mir_text)
        ok = result.get("task_success", 0)
        results.append((tid, task["category"], ok, result.get("error_code", "")))
        print(f"  {'PASS' if ok else 'FAIL'}", flush=True)
        if not ok:
            print(f"  err={result.get('error_code', '?')}", flush=True)
    except Exception as e:
        results.append((tid, task["category"], 0, str(e)))
        print(f"  EXCEPTION: {e}", flush=True)

print(f"\n{'='*50}", flush=True)
total = len(results)
passed = sum(1 for _, _, ok, _ in results if ok)
print(f"TOTAL: {passed}/{total} = {passed/total:.3f}", flush=True)
for tid, cat, ok, err in results:
    print(f"  {tid} ({cat}): {'PASS' if ok else 'FAIL'} {err}", flush=True)
