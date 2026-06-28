#!/usr/bin/env python3
"""Run tasks RW_011 to RW_030."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ollama_client import ollama_generate
from run_generation_eval import compile_expected_payloads, evaluate_candidate, expected_signature, load_jsonl

tasks = load_jsonl(Path(__file__).resolve().parent.parent / "data" / "tasks_realworld.jsonl")
tasks = [t for t in tasks if t["task_id"] >= "RW_011"]
print(f"Loaded {len(tasks)} tasks")

expected_map = compile_expected_payloads(tasks)
print("compile_expected_payloads OK")

prompts = (Path(__file__).resolve().parent.parent / "data" / "prompts_v1.md").read_text(encoding="utf-8")
tag = "```text"
end = "```"
system_start = prompts.index("## 1. System Prompt")
user_start = prompts.index("## 2. User Prompt Template")
system_block = prompts[prompts.index(tag, system_start) + 7:prompts.index(end, prompts.index(tag, system_start) + 7)].strip()
user_block = prompts[prompts.index(tag, user_start) + 7:prompts.index(end, prompts.index(tag, user_start) + 7)].strip()

sig_cache = {t["task_id"]: expected_signature(t) for t in tasks}

results = []
for task in tasks:
    tid = task["task_id"]
    prompt = user_block.format(
        task_id=tid,
        allowed_devices=", ".join(task["allowed_devices"]),
        prompt=task["prompt"],
    )
    print(f"{tid}...", end=" ", flush=True)
    resp = ollama_generate("llama3.1:8b", prompt, system=system_block, temperature=0.0)
    mir_text = resp.get("response", "")
    result = evaluate_candidate(task, expected_map[tid], sig_cache[tid], 1, mir_text)
    ok = result.get("task_success", 0)
    print(f"{'PASS' if ok else 'FAIL'}", flush=True)
    if not ok:
        print(f"  Error: {result.get('error_code', 'unknown')}", flush=True)
    results.append((tid, task["category"], ok))

# Summary
print(f"\n{'='*40}")
total = len(results)
passed = sum(1 for _, _, ok in results if ok)
print(f"Batch 2: {passed}/{total} = {passed/total:.3f}")
for tid, cat, ok in results:
    print(f"  {tid} ({cat}): {'PASS' if ok else 'FAIL'}")
