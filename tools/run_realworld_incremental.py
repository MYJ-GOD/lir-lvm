#!/usr/bin/env python3
"""Run real-world tasks incrementally - saves results after each task."""
import csv
import json
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
close = "```"
system_start = prompts.index("## 1. System Prompt")
user_start = prompts.index("## 2. User Prompt Template")
system_block = prompts[prompts.index(tag, system_start) + 7:prompts.index(close, prompts.index(tag, system_start) + 7)].strip()
user_block = prompts[prompts.index(tag, user_start) + 7:prompts.index(close, prompts.index(tag, user_start) + 7)].strip()

sig_cache = {t["task_id"]: expected_signature(t) for t in tasks}

out_path = Path(__file__).resolve().parent.parent / "result" / "GEN" / "realworld_eval.csv"
out_path.parent.mkdir(parents=True, exist_ok=True)

results = []
for i, task in enumerate(tasks):
    tid = task["task_id"]
    prompt = user_block.format(
        task_id=tid,
        allowed_devices=", ".join(task["allowed_devices"]),
        prompt=task["prompt"],
    )
    print(f"[{i+1}/{len(tasks)}] {tid}...", end=" ", flush=True)
    try:
        resp = ollama_generate("llama3.1:8b", prompt, system=system_block, temperature=0.0, timeout=120.0)
        mir_text = resp.get("response", "")
        result = evaluate_candidate(task, expected_map[tid], sig_cache[tid], 1, mir_text)
        ok = result.get("task_success", 0)
        results.append({
            "task_id": tid,
            "category": task["category"],
            "ir_valid": int(result.get("ir_valid", 0)),
            "compile_pass": int(result.get("compile_pass", 0)),
            "verify_pass": int(result.get("verify_pass", 0)),
            "execution_pass": int(result.get("execution_pass", 0)),
            "task_success": int(ok),
        })
        print(f"{'PASS' if ok else 'FAIL'}", flush=True)
    except Exception as e:
        results.append({
            "task_id": tid,
            "category": task["category"],
            "ir_valid": 0, "compile_pass": 0, "verify_pass": 0,
            "execution_pass": 0, "task_success": 0,
        })
        print(f"ERR: {e}", flush=True)

    # Save incrementally
    with out_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["task_id", "category", "ir_valid", "compile_pass", "verify_pass", "execution_pass", "task_success"])
        writer.writeheader()
        writer.writerows(results)

# Final summary
n = len(results)
metrics = ["ir_valid", "compile_pass", "verify_pass", "execution_pass", "task_success"]
print(f"\n{'='*50}", flush=True)
print(f"Real-World IoT Evaluation ({n} tasks)", flush=True)
print(f"{'='*50}", flush=True)
for m in metrics:
    cnt = sum(r[m] for r in results)
    print(f"  {m}: {cnt}/{n} = {cnt/n:.3f}", flush=True)
